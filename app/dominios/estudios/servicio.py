import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.dominios.autenticacion.servicio import auditar
from app.dominios.estudios.esquemas import (
    ActualizarDisponibilidad,
    ActualizarEstadoOperacional,
    ActualizarEstudio,
    CrearEstudio,
    CrearVersionProtocolo,
    ReconfirmarVigencia,
)
from app.dominios.estudios.modelos import (
    BrazoEstudio,
    CohorteEstudio,
    CriterioManual,
    EstadoEstudio,
    EstadoVersionProtocolo,
    Estudio,
    HistorialEstadoEstudio,
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
        estado_operacional=datos.estado_operacional,
        disponibilidad=datos.disponibilidad,
        estado=EstadoEstudio.BORRADOR,
        disponible=True,
        fuente_informacion=datos.fuente_informacion,
        fecha_corte=datos.fecha_corte,
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
        cohorte = CohorteEstudio(
            estudio_id=estudio.id,
            nombre=cohorte_dato.nombre.strip(),
            descripcion=cohorte_dato.descripcion,
            patologia=cohorte_dato.patologia,
            subtipo_histologico=cohorte_dato.subtipo_histologico,
            escenario_clinico=cohorte_dato.escenario_clinico,
            linea_tratamiento=cohorte_dato.linea_tratamiento,
            biomarcadores_requeridos=cohorte_dato.biomarcadores_requeridos,
            meta_reclutamiento=cohorte_dato.meta_reclutamiento,
            estado_operacional=cohorte_dato.estado_operacional,
            disponibilidad=cohorte_dato.disponibilidad,
        )
        sesion_db.add(cohorte)
        sesion_db.flush()

        for brazo_dato in cohorte_dato.brazos:
            sesion_db.add(
                BrazoEstudio(
                    cohorte_id=cohorte.id,
                    nombre=brazo_dato.nombre.strip(),
                    descripcion=brazo_dato.descripcion,
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


def actualizar_estado_operacional(
    sesion_db: Session,
    estudio: Estudio,
    datos: ActualizarEstadoOperacional,
    *,
    actor_id: uuid.UUID,
    direccion_ip: str | None,
) -> Estudio:
    instante = ahora_utc()
    valor_anterior = estudio.estado_operacional.value
    estudio.estado_operacional = datos.estado_operacional
    estudio.actualizado_en = instante

    historial = HistorialEstadoEstudio(
        estudio_id=estudio.id,
        campo_modificado="estado_operacional",
        valor_anterior=valor_anterior,
        valor_nuevo=datos.estado_operacional.value,
        fecha=instante,
        autor_id=actor_id,
        fuente=datos.fuente.strip(),
        motivo=datos.motivo.strip(),
    )
    sesion_db.add(historial)

    auditar(
        sesion_db,
        accion="estudio.actualizar_estado_operacional",
        entidad="estudio",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=estudio.id,
        direccion_ip=direccion_ip,
        contexto={
            "anterior": valor_anterior,
            "nuevo": datos.estado_operacional.value,
            "motivo": datos.motivo,
        },
    )
    sesion_db.commit()
    sesion_db.refresh(estudio)
    return estudio


def actualizar_disponibilidad(
    sesion_db: Session,
    estudio: Estudio,
    datos: ActualizarDisponibilidad,
    *,
    actor_id: uuid.UUID,
    direccion_ip: str | None,
) -> Estudio:
    instante = ahora_utc()
    valor_anterior = estudio.disponibilidad.value
    estudio.disponibilidad = datos.disponibilidad
    estudio.actualizado_en = instante

    historial = HistorialEstadoEstudio(
        estudio_id=estudio.id,
        campo_modificado="disponibilidad",
        valor_anterior=valor_anterior,
        valor_nuevo=datos.disponibilidad.value,
        fecha=instante,
        autor_id=actor_id,
        fuente=datos.fuente.strip(),
        motivo=datos.motivo.strip(),
    )
    sesion_db.add(historial)

    auditar(
        sesion_db,
        accion="estudio.actualizar_disponibilidad",
        entidad="estudio",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=estudio.id,
        direccion_ip=direccion_ip,
        contexto={
            "anterior": valor_anterior,
            "nuevo": datos.disponibilidad.value,
            "motivo": datos.motivo,
        },
    )
    sesion_db.commit()
    sesion_db.refresh(estudio)
    return estudio


def reconfirmar_vigencia(
    sesion_db: Session,
    estudio: Estudio,
    datos: ReconfirmarVigencia,
    *,
    actor_id: uuid.UUID,
    direccion_ip: str | None,
) -> Estudio:
    instante = ahora_utc()
    estudio.fuente_informacion = datos.fuente_informacion.strip()
    estudio.fecha_corte = datos.fecha_corte or instante
    estudio.verificado_por_id = actor_id
    estudio.fecha_verificacion = instante
    estudio.proxima_revision = instante + timedelta(days=datos.dias_validez)
    estudio.actualizado_en = instante

    auditar(
        sesion_db,
        accion="estudio.reconfirmar_vigencia",
        entidad="estudio",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=estudio.id,
        direccion_ip=direccion_ip,
        contexto={
            "fuente": estudio.fuente_informacion,
            "proxima_revision": estudio.proxima_revision.isoformat(),
        },
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
                alcance=crit.alcance,
                cohorte_id=crit.cohorte_id,
                brazo_id=crit.brazo_id,
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

    version.es_vigente = True
    version.estado = EstadoVersionProtocolo.VIGENTE
    version.publicada_en = instante
    version.publicada_por_id = actor_id

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
