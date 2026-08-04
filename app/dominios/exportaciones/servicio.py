import csv
import hashlib
import io
import json
import uuid
import zipfile
from datetime import UTC, datetime
from typing import Any
from xml.sax.saxutils import escape

from sqlalchemy import select
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.dominios.autenticacion.modelos import Usuario
from app.dominios.autenticacion.servicio import auditar
from app.dominios.cupos.modelos import CupoDemo
from app.dominios.estudios.modelos import Estudio
from app.dominios.exportaciones.esquemas import ENTIDADES_PERMITIDAS, CrearExportacionDemo
from app.dominios.exportaciones.modelos import ExportacionDemo, FormatoExportacion
from app.dominios.operacion.modelos import Tarea
from app.dominios.pacientes.modelos import DiagnosticoDemo, PacienteDemo, PacienteEstudioDemo
from app.dominios.preseleccion.modelos import PreseleccionDemo

MODELOS = {
    "pacientes": PacienteDemo,
    "diagnosticos": DiagnosticoDemo,
    "estudios": Estudio,
    "asociaciones": PacienteEstudioDemo,
    "tareas": Tarea,
    "preselecciones": PreseleccionDemo,
    "cupos": CupoDemo,
}


def generar(
    sesion: Session, datos: CrearExportacionDemo, usuario: Usuario
) -> tuple[ExportacionDemo, bytes, str]:
    entidades = list(dict.fromkeys(datos.entidades))
    invalidas = set(entidades) - ENTIDADES_PERMITIDAS
    if invalidas or not entidades:
        raise ErrorApi(422, "ENTIDAD_INVALIDA", "Seleccione entidades permitidas para exportar.")
    no_sinteticos = sesion.scalar(
        select(PacienteDemo.id).where(PacienteDemo.sintetico.is_(False)).limit(1)
    )
    if no_sinteticos:
        raise ErrorApi(
            409,
            "CONTRATO_SINTETICO_INCUMPLIDO",
            "La exportación se bloqueó por datos no sintéticos.",
        )
    filas: list[dict[str, Any]] = []
    campos: set[str] = set()
    for entidad in entidades:
        modelo = MODELOS[entidad]
        consulta = select(modelo)
        if datos.estudio_id and hasattr(modelo, "estudio_id"):
            consulta = consulta.where(modelo.estudio_id == datos.estudio_id)
        for item in sesion.scalars(consulta).all():
            contenido = _serializar(item)
            campos.update(contenido)
            filas.append({"entidad": entidad, **contenido})
    archivo = _archivo(datos.formato, filas)
    digest = hashlib.sha256(archivo).hexdigest()
    ahora = datetime.now(UTC)
    registro = ExportacionDemo(
        finalidad=datos.finalidad,
        formato=datos.formato,
        filtros={"entidades": entidades, "estudio_id": str(datos.estudio_id or "") or None},
        campos=sorted(campos),
        cantidad=len(filas),
        hash_sha256=digest,
        autor_id=usuario.id,
        creada_en=ahora,
    )
    sesion.add(registro)
    sesion.flush()
    auditar(
        sesion,
        accion="exportacion_demo.generar",
        entidad="exportacion_demo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=registro.id,
        contexto={"formato": datos.formato.value, "cantidad": len(filas), "sha256": digest},
    )
    sesion.commit()
    sesion.refresh(registro)
    return registro, archivo, _tipo_mime(datos.formato)


def _serializar(item: object) -> dict[str, Any]:
    resultado: dict[str, Any] = {}
    inspeccion: Any = inspect(item)
    for columna in inspeccion.mapper.column_attrs:
        valor = getattr(item, columna.key)
        if hasattr(valor, "value"):
            valor = valor.value
        elif isinstance(valor, (datetime, uuid.UUID)):
            valor = str(valor)
        resultado[columna.key] = valor
    return resultado


def _archivo(formato: FormatoExportacion, filas: list[dict[str, Any]]) -> bytes:
    if formato == FormatoExportacion.JSON:
        return json.dumps(filas, ensure_ascii=False, indent=2, default=str).encode()
    if formato == FormatoExportacion.TXT:
        bloques = [
            "\n".join(f"{campo}: {valor}" for campo, valor in fila.items()) for fila in filas
        ]
        return ("EXPORTACIÓN SINTÉTICA CICUC\n\n" + "\n\n---\n\n".join(bloques)).encode()
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(["entidad", "id", "datos_json"])
    for fila in filas:
        escritor.writerow([fila["entidad"], fila.get("id", ""), json.dumps(fila, default=str)])
    if formato == FormatoExportacion.CSV:
        return salida.getvalue().encode("utf-8-sig")
    return _xlsx(salida.getvalue().splitlines())


def _xlsx(lineas_csv: list[str]) -> bytes:
    filas = list(csv.reader(lineas_csv))
    xml_filas = []
    for indice, fila in enumerate(filas, 1):
        celdas = "".join(
            f'<c r="{chr(65 + columna)}{indice}" t="inlineStr"><is><t>{escape(valor)}</t></is></c>'
            for columna, valor in enumerate(fila)
        )
        xml_filas.append(f'<row r="{indice}">{celdas}</row>')
    hoja = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'
        + "".join(xml_filas)
        + "</sheetData></worksheet>"
    )
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as archivo:
        archivo.writestr(
            "[Content_Types].xml",
            '<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>',  # noqa: E501
        )
        archivo.writestr(
            "_rels/.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>',  # noqa: E501
        )
        archivo.writestr(
            "xl/workbook.xml",
            '<?xml version="1.0"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Datos sintéticos" sheetId="1" r:id="rId1"/></sheets></workbook>',  # noqa: E501
        )
        archivo.writestr(
            "xl/_rels/workbook.xml.rels",
            '<?xml version="1.0"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>',  # noqa: E501
        )
        archivo.writestr("xl/worksheets/sheet1.xml", hoja)
    return salida.getvalue()


def _tipo_mime(formato: FormatoExportacion) -> str:
    return {
        FormatoExportacion.XLSX: (  # noqa: E501
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        FormatoExportacion.CSV: "text/csv; charset=utf-8",
        FormatoExportacion.JSON: "application/json",
        FormatoExportacion.TXT: "text/plain; charset=utf-8",
    }[formato]
