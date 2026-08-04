import uuid
from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.dominios.autenticacion.modelos import Usuario
from app.dominios.autenticacion.servicio import auditar
from app.dominios.estudios.modelos import CriterioManual, Estudio, VersionProtocolo
from app.dominios.pacientes.modelos import PacienteDemo
from app.dominios.preseleccion.esquemas import (
    CambiarEstadoPreseleccionDemo,
    CrearPreseleccionDemo,
    EvaluarCriterioDemo,
)
from app.dominios.preseleccion.modelos import (
    EstadoPreseleccionDemo,
    EvaluacionCriterioDemo,
    HistorialPreseleccionDemo,
    PreseleccionDemo,
)

TRANSICIONES = {
    EstadoPreseleccionDemo.PENDIENTE_REVISION: {
        EstadoPreseleccionDemo.EN_REVISION,
        EstadoPreseleccionDemo.CERRADO,
    },
    EstadoPreseleccionDemo.EN_REVISION: {
        EstadoPreseleccionDemo.INFORMACION_INCOMPLETA,
        EstadoPreseleccionDemo.POSIBLE_BARRERA,
        EstadoPreseleccionDemo.POSIBLE_ESTUDIO_REVISAR,
        EstadoPreseleccionDemo.CERRADO,
    },
    EstadoPreseleccionDemo.INFORMACION_INCOMPLETA: {
        EstadoPreseleccionDemo.EN_REVISION,
        EstadoPreseleccionDemo.CERRADO,
    },
    EstadoPreseleccionDemo.POSIBLE_BARRERA: {
        EstadoPreseleccionDemo.EN_REVISION,
        EstadoPreseleccionDemo.CERRADO,
    },
    EstadoPreseleccionDemo.POSIBLE_ESTUDIO_REVISAR: {
        EstadoPreseleccionDemo.EN_REVISION,
        EstadoPreseleccionDemo.DERIVADO_SCREENING_FORMAL,
        EstadoPreseleccionDemo.CERRADO,
    },
    EstadoPreseleccionDemo.DERIVADO_SCREENING_FORMAL: {EstadoPreseleccionDemo.CERRADO},
    EstadoPreseleccionDemo.CERRADO: {EstadoPreseleccionDemo.EN_REVISION},
}


def obtener(sesion: Session, identificador: uuid.UUID) -> PreseleccionDemo:
    item = sesion.get(PreseleccionDemo, identificador)
    if not item:
        raise ErrorApi(404, "RECURSO_NO_ENCONTRADO", "No se encontró la preselección sintética.")
    return item


def crear(sesion: Session, datos: CrearPreseleccionDemo, usuario: Usuario) -> PreseleccionDemo:
    paciente = sesion.get(PacienteDemo, datos.paciente_id)
    estudio = sesion.get(Estudio, datos.estudio_id)
    version = sesion.get(VersionProtocolo, datos.version_id)
    if not paciente or paciente.archivado or not paciente.sintetico:
        raise ErrorApi(422, "PACIENTE_DEMO_INVALIDO", "Se requiere un paciente sintético activo.")
    if not estudio or not version or version.estudio_id != estudio.id:
        raise ErrorApi(
            422, "VERSION_ESTUDIO_INVALIDA", "La versión no pertenece al estudio indicado."
        )
    ahora = datetime.now(UTC)
    item = PreseleccionDemo(
        paciente_id=paciente.id,
        estudio_id=estudio.id,
        version_id=version.id,
        estado=EstadoPreseleccionDemo.PENDIENTE_REVISION,
        creada_por_id=usuario.id,
        creada_en=ahora,
        actualizada_en=ahora,
    )
    sesion.add(item)
    try:
        sesion.flush()
    except IntegrityError as error:
        sesion.rollback()
        raise ErrorApi(
            409, "PRESELECCION_DUPLICADA", "Ya existe una revisión para este paciente y versión."
        ) from error
    sesion.add(
        HistorialPreseleccionDemo(
            preseleccion_id=item.id,
            estado_anterior=None,
            estado_nuevo=item.estado.value,
            motivo=datos.motivo,
            autor_id=usuario.id,
            fecha=ahora,
        )
    )
    auditar(
        sesion,
        accion="preseleccion_demo.crear",
        entidad="preseleccion_demo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=item.id,
    )
    sesion.commit()
    sesion.refresh(item)
    return item


def evaluar(
    sesion: Session,
    item: PreseleccionDemo,
    criterio_id: uuid.UUID,
    datos: EvaluarCriterioDemo,
    usuario: Usuario,
) -> PreseleccionDemo:
    criterio = sesion.get(CriterioManual, criterio_id)
    if not criterio or criterio.version_id != item.version_id:
        raise ErrorApi(
            422, "CRITERIO_VERSION_INVALIDO", "El criterio no pertenece a la versión revisada."
        )
    if item.estado == EstadoPreseleccionDemo.CERRADO:
        raise ErrorApi(
            409, "PRESELECCION_CERRADA", "Reabra la revisión antes de modificar criterios."
        )
    evaluacion = next((e for e in item.evaluaciones if e.criterio_id == criterio_id), None)
    ahora = datetime.now(UTC)
    if evaluacion:
        evaluacion.estado, evaluacion.comentario, evaluacion.fuente = (
            datos.estado,
            datos.comentario,
            datos.fuente,
        )
        evaluacion.autor_id, evaluacion.actualizada_en = usuario.id, ahora
    else:
        sesion.add(
            EvaluacionCriterioDemo(
                preseleccion_id=item.id,
                criterio_id=criterio_id,
                estado=datos.estado,
                comentario=datos.comentario,
                fuente=datos.fuente,
                autor_id=usuario.id,
                actualizada_en=ahora,
            )
        )
    item.actualizada_en = ahora
    auditar(
        sesion,
        accion="preseleccion_demo.evaluar_criterio",
        entidad="preseleccion_demo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=item.id,
        contexto={"criterio_id": str(criterio_id), "estado": datos.estado.value},
    )
    sesion.commit()
    sesion.refresh(item)
    return item


def cambiar_estado(
    sesion: Session, item: PreseleccionDemo, datos: CambiarEstadoPreseleccionDemo, usuario: Usuario
) -> PreseleccionDemo:
    if datos.estado == item.estado or datos.estado not in TRANSICIONES[item.estado]:
        raise ErrorApi(409, "TRANSICION_INVALIDA", "La transición solicitada no está permitida.")
    anterior, ahora = item.estado, datetime.now(UTC)
    item.estado, item.resumen, item.actualizada_en = (
        datos.estado,
        datos.resumen if datos.resumen is not None else item.resumen,
        ahora,
    )
    sesion.add(
        HistorialPreseleccionDemo(
            preseleccion_id=item.id,
            estado_anterior=anterior.value,
            estado_nuevo=datos.estado.value,
            motivo=datos.motivo,
            autor_id=usuario.id,
            fecha=ahora,
        )
    )
    auditar(
        sesion,
        accion="preseleccion_demo.cambiar_estado",
        entidad="preseleccion_demo",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=item.id,
        contexto={"anterior": anterior.value, "nuevo": datos.estado.value, "motivo": datos.motivo},
    )
    sesion.commit()
    sesion.refresh(item)
    return item
