from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dominios.autenticacion.modelos import Usuario
from app.dominios.autenticacion.servicio import auditar
from app.dominios.estudios.modelos import Estudio
from app.dominios.operacion.esquemas import ActualizarTarea, CrearReporte, CrearTarea
from app.dominios.operacion.modelos import EstadoTarea, ReporteOperativo, Tarea


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
    contenido = {
        "estudios": sesion.scalar(select(func.count()).select_from(Estudio)) or 0,
        "tareas_pendientes": sesion.scalar(
            select(func.count()).select_from(Tarea).where(Tarea.estado == EstadoTarea.PENDIENTE)
        )
        or 0,
        "tareas_totales": sesion.scalar(select(func.count()).select_from(Tarea)) or 0,
    }
    reporte = ReporteOperativo(
        nombre=datos.nombre.strip(),
        finalidad=datos.finalidad.strip(),
        fecha_corte=ahora,
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
