import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.dominios.autenticacion.servicio import auditar
from app.dominios.estudios.esquemas import (
    ActualizarEstudio,
    CrearCriterioManual,
    CrearEstudio,
    CrearVersionProtocolo,
)
from app.dominios.estudios.modelos import (
    CohorteEstudio,
    CriterioManual,
    EstadoEstudio,
    EstadoVersionProtocolo,
    Estudio,
    VersionProtocolo,
)


def ahora_utc() -> datetime:
    return datetime.now(UTC)


def crear_estudio(
    sesion_db: Session,
    datos: CrearEstudio,
    *,
    actor_id: uuid.UUID,
    direccion_ip: str | None,
) -> Estudio:
    instante = ahora_utc()
    estudio = Estudio(
        codigo_interno=datos.codigo_interno.strip().upper(),
        titulo=datos.titulo.strip(),
        patrocinador=datos.patrocinador.strip(),
        fase=datos.fase.strip(),
        patologia=datos.patologia.strip(),
        escenario_clinico=datos.escenario_clinico.strip(),
        linea_tratamiento=datos.linea_tratamiento.strip(),
        centro_atencion=datos.centro_atencion.strip(),
        estado=EstadoEstudio.BORRADOR,
        disponible=True,
        observaciones=datos.observaciones,
        investigador_principal_id=datos.investigador_principal_id,
        coordinador_id=datos.coordinador_id,
        creado_en=instante,
        actualizado_en=instante,
    )
    sesion_db.add(estudio)
    try:
        sesion_db.flush()
    except IntegrityError as error:
        sesion_db.rollback()
        raise ErrorApi(
            409,
            "CODIGO_ESTUDIO_EXISTENTE",
            f"Ya existe un estudio registrado con el código '{datos.codigo_interno}'.",
        ) from error

    for cohorte_dato in datos.cohortes:
        sesion_db.add(
            CohorteEstudio(
                estudio_id=estudio.id,
                nombre=cohorte_dato.nombre.strip(),
                descripcion=cohorte_dato.descripcion,
                biomarcadores_requeridos=cohorte_dato.biomarcadores_requeridos,
                meta_reclutamiento=cohorte_dato.meta_reclutamiento,
            )
        )

    auditar(
        sesion_db,
        accion="estudio.crear",
        entidad="estudio",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=estudio.id,
        direccion_ip=direccion_ip,
        contexto={"codigo": estudio.codigo_interno, "titulo": estudio.titulo},
    )
    sesion_db.commit()
    sesion_db.refresh(estudio)
    return estudio


def actualizar_estudio(
    sesion_db: Session,
    estudio: Estudio,
    datos: ActualizarEstudio,
    *,
    actor_id: uuid.UUID,
    direccion_ip: str | None,
) -> Estudio:
    instante = ahora_utc()
    cambios = datos.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        if valor is not None:
            if isinstance(valor, str):
                valor = valor.strip()
            setattr(estudio, campo, valor)
    estudio.actualizado_en = instante

    auditar(
        sesion_db,
        accion="estudio.actualizar",
        entidad="estudio",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=estudio.id,
        direccion_ip=direccion_ip,
        contexto={"campos_modificados": list(cambios.keys())},
    )
    sesion_db.commit()
    sesion_db.refresh(estudio)
    return estudio


def crear_version_protocolo(
    sesion_db: Session,
    estudio: Estudio,
    datos: CrearVersionProtocolo,
    *,
    actor_id: uuid.UUID,
    direccion_ip: str | None,
) -> VersionProtocolo:
    instante = ahora_utc()
    version = VersionProtocolo(
        estudio_id=estudio.id,
        numero_version=datos.numero_version.strip(),
        descripcion_cambios=datos.descripcion_cambios.strip(),
        estado=EstadoVersionProtocolo.BORRADOR,
        es_vigente=False,
        creada_en=instante,
        creada_por_id=actor_id,
    )
    sesion_db.add(version)
    try:
        sesion_db.flush()
    except IntegrityError as error:
        sesion_db.rollback()
        raise ErrorApi(
            409,
            "NUMERO_VERSION_EXISTENTE",
            f"La versión '{datos.numero_version}' ya existe para este estudio.",
        ) from error

    for crit in datos.criterios:
        sesion_db.add(
            CriterioManual(
                version_id=version.id,
                tipo=crit.tipo,
                orden=crit.orden,
                codigo_criterio=crit.codigo_criterio.strip().upper(),
                descripcion=crit.descripcion.strip(),
                seccion_fuente=crit.seccion_fuente.strip() if crit.seccion_fuente else None,
                observaciones=crit.observaciones,
            )
        )

    auditar(
        sesion_db,
        accion="protocolo.crear_version",
        entidad="version_protocolo",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=version.id,
        direccion_ip=direccion_ip,
        contexto={"numero_version": version.numero_version, "estudio_id": str(estudio.id)},
    )
    sesion_db.commit()
    sesion_db.refresh(version)
    return version


def publicar_version_protocolo(
    sesion_db: Session,
    version: VersionProtocolo,
    *,
    actor_id: uuid.UUID,
    direccion_ip: str | None,
) -> VersionProtocolo:
    instante = ahora_utc()
    estudio = version.estudio

    # Regla de inmutabilidad y transición:
    # 1. Marcar cualquier versión vigente previa como REEMPLAZADA y no vigente.
    sesion_db.execute(
        update(VersionProtocolo)
        .where(
            VersionProtocolo.estudio_id == estudio.id,
            VersionProtocolo.es_vigente.is_(True),
        )
        .values(
            es_vigente=False,
            estado=EstadoVersionProtocolo.REEMPLAZADA,
        )
    )

    # 2. Publicar la versión seleccionada como VIGENTE.
    version.es_vigente = True
    version.estado = EstadoVersionProtocolo.VIGENTE
    version.publicada_en = instante
    version.publicada_por_id = actor_id

    # 3. Si el estudio estaba en borrador o revisión, pasa a VIGENTE.
    if estudio.estado in (EstadoEstudio.BORRADOR, EstadoEstudio.EN_REVISION):
        estudio.estado = EstadoEstudio.VIGENTE
        estudio.actualizado_en = instante

    auditar(
        sesion_db,
        accion="protocolo.publicar_version",
        entidad="version_protocolo",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=version.id,
        direccion_ip=direccion_ip,
        contexto={"numero_version": version.numero_version, "estudio_id": str(estudio.id)},
    )
    sesion_db.commit()
    sesion_db.refresh(version)
    return version
