"""importar_catalogo_csv.py — HU-035: Importación sanitizada de inventario oncológico real."""

import csv
import sys
from datetime import UTC, datetime

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.base_datos.sesion import FabricaSesiones
from app.dominios.autenticacion.modelos import Usuario
from app.dominios.autenticacion.servicio import normalizar_correo
from app.dominios.estudios.esquemas import CrearEstudio
from app.dominios.estudios.modelos import (
    EstadoDisponibilidadEstudio,
    EstadoOperacionalEstudio,
    Estudio,
)
from app.dominios.estudios.servicio import crear_estudio

COLUMNAS_PROHIBIDAS = {"paciente", "nombre_paciente", "rut", "telefono", "email_paciente"}


class FilaCatalogoSanitizado(BaseModel):
    codigo_interno: str = Field(min_length=1, max_length=64)
    titulo: str = Field(min_length=1, max_length=256)
    patrocinador: str = Field(min_length=1, max_length=120)
    fase: str = Field(min_length=1, max_length=64)
    patologia: str = Field(min_length=1, max_length=120)
    escenario_clinico: str = Field(min_length=1, max_length=120)
    linea_tratamiento: str = Field(min_length=1, max_length=64)
    centro_atencion: str = Field(default="CICUC Principal")
    estado_operacional: EstadoOperacionalEstudio = Field(
        default=EstadoOperacionalEstudio.SIN_CONFIRMAR
    )
    disponibilidad: EstadoDisponibilidadEstudio = Field(
        default=EstadoDisponibilidadEstudio.SIN_CONFIRMAR
    )
    fuente_informacion: str = Field(default="Catálogo Oficial Oncología CICUC")


def importar_csv(ruta_csv: str, *, dry_run: bool = False) -> None:
    print(f"--- Modo: {'DRY-RUN (Simulación sin escribir)' if dry_run else 'IMPORTACIÓN REAL'} ---")
    with open(ruta_csv, encoding="utf-8") as f:
        lector = csv.DictReader(f)
        columnas = {c.strip().lower() for c in (lector.fieldnames or [])}

        # Validación de columnas prohibidas de datos de pacientes (HU-035)
        interseccion = columnas.intersection(COLUMNAS_PROHIBIDAS)
        if interseccion:
            raise SystemExit(
                f"ERROR DE SEGURIDAD HU-035: Se detectaron columnas prohibidas: {interseccion}"
            )

        filas_validas = []
        errores = []
        for idx, fila in enumerate(lector, start=2):
            try:
                item = FilaCatalogoSanitizado.model_validate(fila)
                filas_validas.append(item)
            except Exception as e:
                errores.append(f"Fila {idx}: {e}")

        if errores:
            print(f"Se encontraron {len(errores)} errores de validación:")
            for err in errores:
                print(f" - {err}")
            raise SystemExit("Importación cancelada por errores en el archivo CSV.")

        print(f"Archivo verificado correctamente. {len(filas_validas)} filas listas para procesar.")

        if dry_run:
            print("Simulación (dry-run) completada con éxito.")
            return

        with FabricaSesiones() as sesion:
            admin = sesion.scalar(
                select(Usuario).where(Usuario.correo == normalizar_correo("admin@cicuc.cl"))
            )
            if not admin:
                raise SystemExit("No existe usuario 'admin@cicuc.cl' autor de la importación.")

            creados = 0
            omitidos = 0
            for item in filas_validas:
                cod_normalizado = item.codigo_interno.strip().upper()
                existente = sesion.scalar(
                    select(Estudio).where(Estudio.codigo_interno == cod_normalizado)
                )
                if existente:
                    omitidos += 1
                    continue

                crear_estudio(
                    sesion,
                    CrearEstudio(
                        codigo_interno=item.codigo_interno,
                        titulo=item.titulo,
                        patrocinador=item.patrocinador,
                        fase=item.fase,
                        patologia=item.patologia,
                        escenario_clinico=item.escenario_clinico,
                        linea_tratamiento=item.linea_tratamiento,
                        centro_atencion=item.centro_atencion,
                        estado_operacional=item.estado_operacional,
                        disponibilidad=item.disponibilidad,
                        fuente_informacion=item.fuente_informacion,
                        fecha_corte=datetime.now(UTC),
                    ),
                    actor_id=admin.id,
                    direccion_ip="127.0.0.1",
                )
                creados += 1

            print(f"Importación finalizada. Creados: {creados}, Omitidos: {omitidos}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python -m app.scripts.importar_catalogo_csv <ruta_archivo.csv> [--dry-run]")
        sys.exit(1)

    ruta = sys.argv[1]
    es_dry_run = "--dry-run" in sys.argv
    importar_csv(ruta, dry_run=es_dry_run)
