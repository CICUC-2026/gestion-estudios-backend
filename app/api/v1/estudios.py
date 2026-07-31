import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.errores import ErrorApi
from app.dominios.autenticacion.dependencias import (
    SesionDb,
    UsuarioActual,
    requerir_roles,
)
from app.dominios.autenticacion.modelos import RolUsuario, Usuario
from app.dominios.estudios.esquemas import (
    ActualizarDisponibilidad,
    ActualizarEstadoOperacional,
    ActualizarEstudio,
    ComparacionVersionesRespuesta,
    CrearEstudio,
    CrearVersionProtocolo,
    CriterioManualRespuesta,
    EstudioRespuesta,
    ReconfirmarVigencia,
    VersionProtocoloRespuesta,
)
from app.dominios.estudios.modelos import (
    CohorteEstudio,
    EstadoDisponibilidadEstudio,
    EstadoEstudio,
    EstadoOperacionalEstudio,
    Estudio,
    EtiquetaVigencia,
    VersionProtocolo,
)
from app.dominios.estudios.servicio import (
    actualizar_disponibilidad,
    actualizar_estado_operacional,
    actualizar_estudio,
    crear_estudio,
    crear_version_protocolo,
    publicar_version_protocolo,
    reconfirmar_vigencia,
)

router = APIRouter(prefix="/estudios", tags=["estudios"])

PermisoGestionEstudio = Annotated[
    Usuario,
    Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR,
            RolUsuario.COORDINADOR,
            RolUsuario.INVESTIGADOR_PRINCIPAL,
        )
    ),
]

PermisoAprobarProtocolo = Annotated[
    Usuario,
    Depends(
        requerir_roles(
            RolUsuario.ADMINISTRADOR,
            RolUsuario.INVESTIGADOR_PRINCIPAL,
        )
    ),
]


def _obtener_estudio_o_404(sesion_db: SesionDb, estudio_id: uuid.UUID) -> Estudio:
    estudio = sesion_db.scalar(
        select(Estudio)
        .options(
            selectinload(Estudio.cohortes).selectinload(CohorteEstudio.brazos),
            selectinload(Estudio.versiones).selectinload(VersionProtocolo.criterios),
            selectinload(Estudio.historial_estados),
        )
        .where(Estudio.id == estudio_id)
    )
    if not estudio:
        raise ErrorApi(404, "ESTUDIO_NO_ENCONTRADO", "No se encontró el estudio clínico.")
    return estudio


def _serializar_estudio(estudio: Estudio) -> EstudioRespuesta:
    res = EstudioRespuesta.model_validate(estudio)
    version_v = next((v for v in estudio.versiones if v.es_vigente), None)
    if version_v:
        res.version_vigente = VersionProtocoloRespuesta.model_validate(version_v)
    return res


@router.get("", response_model=list[EstudioRespuesta])
def listar_estudios(
    sesion_db: SesionDb,
    usuario: UsuarioActual,
    patologia: Annotated[str | None, Query()] = None,
    estado: Annotated[EstadoEstudio | None, Query()] = None,
    estado_operacional: Annotated[EstadoOperacionalEstudio | None, Query()] = None,
    disponibilidad: Annotated[EstadoDisponibilidadEstudio | None, Query()] = None,
    vigencia: Annotated[EtiquetaVigencia | None, Query()] = None,
) -> list[EstudioRespuesta]:
    consulta = select(Estudio).options(
        selectinload(Estudio.cohortes).selectinload(CohorteEstudio.brazos),
        selectinload(Estudio.versiones).selectinload(VersionProtocolo.criterios),
        selectinload(Estudio.historial_estados),
    )
    if patologia:
        consulta = consulta.where(Estudio.patologia.ilike(f"%{patologia}%"))
    if estado:
        consulta = consulta.where(Estudio.estado == estado)
    if estado_operacional:
        consulta = consulta.where(Estudio.estado_operacional == estado_operacional)
    if disponibilidad:
        consulta = consulta.where(Estudio.disponibilidad == disponibilidad)

    consulta = consulta.order_by(Estudio.creado_en.desc())
    estudios = sesion_db.scalars(consulta).all()

    resultado = [_serializar_estudio(e) for e in estudios]
    if vigencia:
        resultado = [e for e in resultado if e.etiqueta_vigencia == vigencia]
    return resultado


@router.post("", response_model=EstudioRespuesta, status_code=201)
def registrar_estudio(
    datos: CrearEstudio,
    request: Request,
    sesion_db: SesionDb,
    autorizado: PermisoGestionEstudio,
) -> EstudioRespuesta:
    estudio = crear_estudio(
        sesion_db,
        datos,
        actor_id=autorizado.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return _serializar_estudio(estudio)


@router.get("/{estudio_id}", response_model=EstudioRespuesta)
def obtener_estudio(
    estudio_id: uuid.UUID,
    sesion_db: SesionDb,
    usuario: UsuarioActual,
) -> EstudioRespuesta:
    estudio = _obtener_estudio_o_404(sesion_db, estudio_id)
    return _serializar_estudio(estudio)


@router.patch("/{estudio_id}", response_model=EstudioRespuesta)
def modificar_estudio(
    estudio_id: uuid.UUID,
    datos: ActualizarEstudio,
    request: Request,
    sesion_db: SesionDb,
    autorizado: PermisoGestionEstudio,
) -> EstudioRespuesta:
    estudio = _obtener_estudio_o_404(sesion_db, estudio_id)
    estudio = actualizar_estudio(
        sesion_db,
        estudio,
        datos,
        actor_id=autorizado.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return _serializar_estudio(estudio)


@router.patch("/{estudio_id}/estado-operacional", response_model=EstudioRespuesta)
def cambiar_estado_operacional(
    estudio_id: uuid.UUID,
    datos: ActualizarEstadoOperacional,
    request: Request,
    sesion_db: SesionDb,
    autorizado: PermisoGestionEstudio,
) -> EstudioRespuesta:
    estudio = _obtener_estudio_o_404(sesion_db, estudio_id)
    estudio = actualizar_estado_operacional(
        sesion_db,
        estudio,
        datos,
        actor_id=autorizado.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return _serializar_estudio(estudio)


@router.patch("/{estudio_id}/disponibilidad", response_model=EstudioRespuesta)
def cambiar_disponibilidad(
    estudio_id: uuid.UUID,
    datos: ActualizarDisponibilidad,
    request: Request,
    sesion_db: SesionDb,
    autorizado: PermisoGestionEstudio,
) -> EstudioRespuesta:
    estudio = _obtener_estudio_o_404(sesion_db, estudio_id)
    estudio = actualizar_disponibilidad(
        sesion_db,
        estudio,
        datos,
        actor_id=autorizado.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return _serializar_estudio(estudio)


@router.post("/{estudio_id}/reconfirmar-vigencia", response_model=EstudioRespuesta)
def ejecutar_reconfirmacion_vigencia(
    estudio_id: uuid.UUID,
    datos: ReconfirmarVigencia,
    request: Request,
    sesion_db: SesionDb,
    autorizado: PermisoGestionEstudio,
) -> EstudioRespuesta:
    estudio = _obtener_estudio_o_404(sesion_db, estudio_id)
    estudio = reconfirmar_vigencia(
        sesion_db,
        estudio,
        datos,
        actor_id=autorizado.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return _serializar_estudio(estudio)


@router.post("/{estudio_id}/versiones", response_model=VersionProtocoloRespuesta, status_code=201)
def agregar_version(
    estudio_id: uuid.UUID,
    datos: CrearVersionProtocolo,
    request: Request,
    sesion_db: SesionDb,
    autorizado: PermisoGestionEstudio,
) -> VersionProtocoloRespuesta:
    estudio = _obtener_estudio_o_404(sesion_db, estudio_id)
    version = crear_version_protocolo(
        sesion_db,
        estudio,
        datos,
        actor_id=autorizado.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return VersionProtocoloRespuesta.model_validate(version)


@router.post(
    "/{estudio_id}/versiones/{version_id}/publicar",
    response_model=VersionProtocoloRespuesta,
)
def publicar_version(
    estudio_id: uuid.UUID,
    version_id: uuid.UUID,
    request: Request,
    sesion_db: SesionDb,
    autorizado: PermisoAprobarProtocolo,
) -> VersionProtocoloRespuesta:
    estudio = _obtener_estudio_o_404(sesion_db, estudio_id)
    version = next((v for v in estudio.versiones if v.id == version_id), None)
    if not version:
        raise ErrorApi(404, "VERSION_NO_ENCONTRADA", "No se encontró la versión de protocolo.")

    version_publicada = publicar_version_protocolo(
        sesion_db,
        version,
        actor_id=autorizado.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return VersionProtocoloRespuesta.model_validate(version_publicada)


@router.get(
    "/{estudio_id}/comparar-versiones",
    response_model=ComparacionVersionesRespuesta,
)
def comparar_versiones(
    estudio_id: uuid.UUID,
    version_v1_id: uuid.UUID,
    version_v2_id: uuid.UUID,
    sesion_db: SesionDb,
    usuario: UsuarioActual,
) -> ComparacionVersionesRespuesta:
    estudio = _obtener_estudio_o_404(sesion_db, estudio_id)
    v1 = next((v for v in estudio.versiones if v.id == version_v1_id), None)
    v2 = next((v for v in estudio.versiones if v.id == version_v2_id), None)

    if not v1 or not v2:
        raise ErrorApi(
            404,
            "VERSIONES_INVALIDAS",
            "Ambas versiones deben existir para ser comparadas.",
        )

    crit_v1_map = {c.codigo_criterio: c for c in v1.criterios}
    crit_v2_map = {c.codigo_criterio: c for c in v2.criterios}

    agregados = [
        CriterioManualRespuesta.model_validate(c)
        for cod, c in crit_v2_map.items()
        if cod not in crit_v1_map
    ]
    eliminados = [
        CriterioManualRespuesta.model_validate(c)
        for cod, c in crit_v1_map.items()
        if cod not in crit_v2_map
    ]

    modificados = []
    for cod in crit_v1_map.keys() & crit_v2_map.keys():
        c1 = crit_v1_map[cod]
        c2 = crit_v2_map[cod]
        if c1.descripcion != c2.descripcion or c1.tipo != c2.tipo:
            modificados.append(
                {
                    "anterior": CriterioManualRespuesta.model_validate(c1),
                    "nuevo": CriterioManualRespuesta.model_validate(c2),
                }
            )

    return ComparacionVersionesRespuesta(
        estudio_id=estudio_id,
        version_anterior=VersionProtocoloRespuesta.model_validate(v1),
        version_nueva=VersionProtocoloRespuesta.model_validate(v2),
        criterios_agregados=agregados,
        criterios_eliminados=eliminados,
        criterios_modificados=modificados,
    )
