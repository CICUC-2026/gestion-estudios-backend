from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.dominios.autenticacion.modelos import Usuario
from app.dominios.autenticacion.servicio import auditar
from app.dominios.cupos.modelos import CupoDemo, EstadoCupoDemo
from app.dominios.estudios.modelos import Estudio
from app.dominios.operacion.esquemas import ActualizarTarea, CrearReporte, CrearTarea
from app.dominios.operacion.modelos import EstadoTarea, ReporteOperativo, Tarea
from app.dominios.pacientes.modelos import PacienteDemo, PacienteEstudioDemo
from app.dominios.preseleccion.modelos import PreseleccionDemo


def crear_tarea(sesion: Session, datos: CrearTarea, usuario: Usuario) -> Tarea:
    ahora = datetime.now(UTC)
    tarea = Tarea(
        titulo=datos.titulo.strip(),
        descripcion=datos.descripcion,
        prioridad=datos.prioridad,
        estado=EstadoTarea.PENDIENTE,
        vence_en=datos.vence_en,
        creada_por_id=usuario.id,
        responsable_id=datos.responsable_id or usuario.id,
        paciente_id=datos.paciente_id,
        estudio_id=datos.estudio_id,
        creada_en=ahora,
        actualizada_en=ahora,
    )
    sesion.add(tarea)
    sesion.flush()
    auditar(
        sesion,
        accion="tarea.crear",
        entidad="tarea",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=tarea.id,
    )
    sesion.commit()
    sesion.refresh(tarea)
    return tarea


def actualizar_tarea(
    sesion: Session, tarea: Tarea, datos: ActualizarTarea, usuario: Usuario
) -> Tarea:
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(
            tarea, campo, valor.strip() if campo == "titulo" and isinstance(valor, str) else valor
        )
    tarea.actualizada_en = datetime.now(UTC)
    auditar(
        sesion,
        accion="tarea.actualizar",
        entidad="tarea",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=tarea.id,
        contexto=datos.model_dump(mode="json", exclude_unset=True),
    )
    sesion.commit()
    sesion.refresh(tarea)
    return tarea


def preparar_reporte(sesion: Session, datos: CrearReporte, usuario: Usuario) -> ReporteOperativo:
    ahora = datetime.now(UTC)
    corte = datos.fecha_corte or ahora
    if corte > ahora:
        from app.api.errores import ErrorApi

        raise ErrorApi(422, "CORTE_FUTURO", "La fecha de corte no puede estar en el futuro.")

    def contar(consulta: Select[Any]) -> int:
        return sesion.scalar(select(func.count()).select_from(consulta.subquery())) or 0

    filtro_estudio = datos.estudio_id
    tareas = select(Tarea.id).where(Tarea.creada_en <= corte)
    if filtro_estudio:
        tareas = tareas.where(Tarea.estudio_id == filtro_estudio)
    if datos.estados_tarea:
        tareas = tareas.where(Tarea.estado.in_(datos.estados_tarea))
    estudios = select(Estudio.id).where(Estudio.creado_en <= corte)
    asociaciones = select(PacienteEstudioDemo.id).where(PacienteEstudioDemo.creado_en <= corte)
    preselecciones = select(PreseleccionDemo.id).where(PreseleccionDemo.creada_en <= corte)
    cupos = select(CupoDemo.id).where(CupoDemo.creado_en <= corte)
    if filtro_estudio:
        estudios = estudios.where(Estudio.id == filtro_estudio)
        asociaciones = asociaciones.where(PacienteEstudioDemo.estudio_id == filtro_estudio)
        preselecciones = preselecciones.where(PreseleccionDemo.estudio_id == filtro_estudio)
        cupos = cupos.where(CupoDemo.estudio_id == filtro_estudio)

    def metrica(cantidad: int, estado: str = "confirmado") -> dict[str, object]:
        visible = cantidad == 0 or cantidad >= 5
        return {
            "valor": cantidad if visible else None,
            "presentacion": str(cantidad) if visible else "<5",
            "estado": estado,
            "suprimido": not visible,
        }

    total_tareas = contar(tareas)
    pendientes = contar(tareas.where(Tarea.estado == EstadoTarea.PENDIENTE))
    total_estudios = contar(estudios)
    total_asociaciones = contar(asociaciones)
    total_preselecciones = contar(preselecciones)
    total_cupos = contar(cupos)
    cupos_desactualizados = contar(
        cupos.where(CupoDemo.estado == EstadoCupoDemo.PENDIENTE_RECONFIRMACION)
    )
    pacientes = contar(
        select(PacienteDemo.id).where(
            PacienteDemo.creado_en <= corte, PacienteDemo.sintetico.is_(True)
        )
    )
    contenido = {
        "estudios": total_estudios,
        "tareas_pendientes": pendientes,
        "tareas_totales": total_tareas,
        "version_catalogo": "2026-08-04",
        "definicion": "Conteos administrativos sintéticos existentes a la fecha de corte.",
        "fecha_corte": corte.isoformat(),
        "filtros": {
            "estudio_id": str(filtro_estudio) if filtro_estudio else None,
            "estados_tarea": [estado.value for estado in datos.estados_tarea],
        },
        "politica_supresion": "Los grupos entre 1 y 4 se presentan como <5.",
        "campos": [
            "estudios",
            "pacientes_sinteticos",
            "reclutamiento_administrativo",
            "preselecciones_manuales",
            "cupos",
            "cupos_desactualizados",
            "tareas",
        ],
        "metricas": {
            "estudios": metrica(total_estudios),
            "pacientes_sinteticos": metrica(pacientes),
            "reclutamiento_administrativo": metrica(total_asociaciones, "tentativo"),
            "lista_espera": {**metrica(0, "sin_fuente"), "nota": "Dominio no implementado"},
            "preselecciones_manuales": metrica(total_preselecciones, "tentativo"),
            "cupos": metrica(total_cupos),
            "cupos_desactualizados": metrica(cupos_desactualizados, "desactualizado"),
            "tareas": metrica(total_tareas),
            "tareas_pendientes": metrica(pendientes, "tentativo"),
        },
        "advertencia": "Uso operativo; no expresa eficacia, elegibilidad ni riesgo clínico.",
    }
    reporte = ReporteOperativo(
        nombre=datos.nombre.strip(),
        finalidad=datos.finalidad.strip(),
        fecha_corte=corte,
        contenido=contenido,
        creado_por_id=usuario.id,
        creado_en=ahora,
    )
    sesion.add(reporte)
    sesion.flush()
    auditar(
        sesion,
        accion="reporte.preparar",
        entidad="reporte_operativo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=reporte.id,
    )
    sesion.commit()
    sesion.refresh(reporte)
    return reporte
