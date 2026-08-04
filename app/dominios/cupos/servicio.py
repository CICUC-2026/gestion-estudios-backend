import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.dominios.autenticacion.modelos import Usuario
from app.dominios.autenticacion.servicio import auditar
from app.dominios.cupos.esquemas import CambiarCupoDemo, CrearCupoDemo
from app.dominios.cupos.modelos import CupoDemo, EstadoCupoDemo, HistorialCupoDemo
from app.dominios.estudios.modelos import Estudio
from app.dominios.pacientes.modelos import PacienteDemo

TRANSICIONES = {
    EstadoCupoDemo.CONFIRMADO: {
        EstadoCupoDemo.RESERVADO,
        EstadoCupoDemo.PENDIENTE_RECONFIRMACION,
        EstadoCupoDemo.CANCELADO,
    },
    EstadoCupoDemo.RESERVADO: {
        EstadoCupoDemo.OCUPADO,
        EstadoCupoDemo.CONFIRMADO,
        EstadoCupoDemo.PENDIENTE_RECONFIRMACION,
        EstadoCupoDemo.CANCELADO,
    },
    EstadoCupoDemo.OCUPADO: {EstadoCupoDemo.PENDIENTE_RECONFIRMACION, EstadoCupoDemo.CANCELADO},
    EstadoCupoDemo.PENDIENTE_RECONFIRMACION: {
        EstadoCupoDemo.CONFIRMADO,
        EstadoCupoDemo.RESERVADO,
        EstadoCupoDemo.CANCELADO,
    },
    EstadoCupoDemo.CANCELADO: set(),
}


def obtener(sesion: Session, identificador: uuid.UUID) -> CupoDemo:
    item = sesion.get(CupoDemo, identificador)
    if not item:
        raise ErrorApi(404, "RECURSO_NO_ENCONTRADO", "No se encontró el cupo sintético.")
    return item


def listar(sesion: Session) -> list[CupoDemo]:
    actualizar_vencidos(sesion)
    return list(sesion.scalars(select(CupoDemo).order_by(CupoDemo.creado_en.desc())).unique().all())


def crear(sesion: Session, datos: CrearCupoDemo, usuario: Usuario) -> CupoDemo:
    if not sesion.get(Estudio, datos.estudio_id):
        raise ErrorApi(422, "ESTUDIO_INVALIDO", "El estudio indicado no existe.")
    ahora = datetime.now(UTC)
    item = CupoDemo(
        estudio_id=datos.estudio_id,
        paciente_id=None,
        estado=EstadoCupoDemo.CONFIRMADO,
        fuente=datos.fuente,
        responsable_id=usuario.id,
        dias_validez=datos.dias_validez,
        confirmado_en=ahora,
        vence_en=ahora + timedelta(days=datos.dias_validez),
        creado_en=ahora,
        actualizado_en=ahora,
    )
    sesion.add(item)
    sesion.flush()
    _historial(sesion, item, None, datos.motivo, usuario.id, ahora)
    _auditar(sesion, item, usuario, "crear", None)
    sesion.commit()
    sesion.refresh(item)
    return item


def cambiar(sesion: Session, item: CupoDemo, datos: CambiarCupoDemo, usuario: Usuario) -> CupoDemo:
    if datos.estado == item.estado or datos.estado not in TRANSICIONES[item.estado]:
        raise ErrorApi(409, "TRANSICION_INVALIDA", "La transición solicitada no está permitida.")
    paciente_id = datos.paciente_id if datos.paciente_id is not None else item.paciente_id
    if datos.estado in {EstadoCupoDemo.RESERVADO, EstadoCupoDemo.OCUPADO}:
        paciente = sesion.get(PacienteDemo, paciente_id) if paciente_id else None
        if not paciente or paciente.archivado or not paciente.sintetico:
            raise ErrorApi(
                422, "PACIENTE_DEMO_INVALIDO", "Se requiere un paciente sintético activo."
            )
    if datos.estado == EstadoCupoDemo.CONFIRMADO:
        paciente_id = None
    ahora, anterior = datetime.now(UTC), item.estado
    if datos.dias_validez is not None or datos.estado in {
        EstadoCupoDemo.CONFIRMADO,
        EstadoCupoDemo.RESERVADO,
    }:
        dias = datos.dias_validez or 30
        item.dias_validez = dias
        item.confirmado_en = ahora
        item.vence_en = ahora + timedelta(days=dias)
    item.estado = datos.estado
    item.paciente_id = paciente_id
    item.responsable_id = usuario.id
    item.actualizado_en = ahora
    if datos.fuente is not None:
        item.fuente = datos.fuente
    _historial(sesion, item, anterior, datos.motivo, usuario.id, ahora)
    _auditar(sesion, item, usuario, "cambiar_estado", anterior)
    sesion.commit()
    sesion.refresh(item)
    return item


def actualizar_vencidos(sesion: Session) -> int:
    ahora = datetime.now(UTC)
    items = sesion.scalars(
        select(CupoDemo).where(
            CupoDemo.vence_en <= ahora,
            CupoDemo.estado.in_(
                [EstadoCupoDemo.CONFIRMADO, EstadoCupoDemo.RESERVADO, EstadoCupoDemo.OCUPADO]
            ),
        )
    ).all()
    for item in items:
        anterior = item.estado
        item.estado = EstadoCupoDemo.PENDIENTE_RECONFIRMACION
        item.actualizado_en = ahora
        _historial(sesion, item, anterior, "Vigencia vencida; requiere reconfirmación", None, ahora)
        auditar(
            sesion,
            accion="cupo_demo.vencer",
            entidad="cupo_demo",
            resultado="exito",
            entidad_id=item.id,
            contexto={
                "anterior": anterior.value,
                "paciente_conservado": str(item.paciente_id or ""),
            },
        )
    if items:
        sesion.commit()
    return len(items)


def _historial(
    sesion: Session,
    item: CupoDemo,
    anterior: EstadoCupoDemo | None,
    motivo: str,
    autor_id: uuid.UUID | None,
    fecha: datetime,
) -> None:
    sesion.add(
        HistorialCupoDemo(
            cupo_id=item.id,
            estado_anterior=anterior.value if anterior else None,
            estado_nuevo=item.estado.value,
            paciente_id=item.paciente_id,
            motivo=motivo,
            autor_id=autor_id,
            fecha=fecha,
        )
    )


def _auditar(
    sesion: Session,
    item: CupoDemo,
    usuario: Usuario,
    accion: str,
    anterior: EstadoCupoDemo | None,
) -> None:
    auditar(
        sesion,
        accion=f"cupo_demo.{accion}",
        entidad="cupo_demo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=item.id,
        contexto={
            "anterior": anterior.value if anterior else None,
            "nuevo": item.estado.value,
            "paciente_id": str(item.paciente_id or ""),
        },
    )
