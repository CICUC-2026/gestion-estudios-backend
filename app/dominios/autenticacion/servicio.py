import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.configuracion.ajustes import Ajustes
from app.dominios.autenticacion.esquemas import CrearUsuario
from app.dominios.autenticacion.modelos import (
    RegistroAuditoria,
    RolUsuario,
    Sesion,
    Usuario,
    UsuarioRol,
)

_verificador = PasswordHasher()
_hash_ficticio = _verificador.hash("valor-ficticio-para-tiempo-constante")


def ahora_utc() -> datetime:
    return datetime.now(UTC)


def normalizar_correo(correo: str) -> str:
    return correo.strip().casefold()


def crear_hash_contrasena(contrasena: str) -> str:
    return _verificador.hash(contrasena)


def verificar_contrasena(contrasena_hash: str, contrasena: str) -> bool:
    try:
        return _verificador.verify(contrasena_hash, contrasena)
    except (VerifyMismatchError, InvalidHashError):
        return False


def crear_token() -> tuple[str, str]:
    token = secrets.token_urlsafe(48)
    return token, hash_token(token)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def auditar(
    sesion_db: Session,
    *,
    accion: str,
    entidad: str,
    resultado: str,
    usuario_id: uuid.UUID | None = None,
    entidad_id: uuid.UUID | None = None,
    direccion_ip: str | None = None,
    contexto: dict[str, Any] | None = None,
) -> None:
    sesion_db.add(
        RegistroAuditoria(
            usuario_id=usuario_id,
            accion=accion,
            entidad=entidad,
            entidad_id=str(entidad_id) if entidad_id else None,
            fecha=ahora_utc(),
            direccion_ip=direccion_ip,
            resultado=resultado,
            contexto=contexto or {},
        )
    )


def crear_usuario(
    sesion_db: Session,
    datos: CrearUsuario,
    *,
    actor_id: uuid.UUID | None,
    direccion_ip: str | None,
) -> Usuario:
    instante = ahora_utc()
    usuario = Usuario(
        nombres=datos.nombres.strip(),
        apellidos=datos.apellidos.strip(),
        correo=normalizar_correo(str(datos.correo)),
        contrasena_hash=crear_hash_contrasena(datos.contrasena_inicial),
        es_administrador_sistema=datos.es_administrador_sistema,
        activo=True,
        intentos_fallidos=0,
        creado_en=instante,
        actualizado_en=instante,
    )
    sesion_db.add(usuario)
    try:
        sesion_db.flush()
    except IntegrityError as error:
        sesion_db.rollback()
        raise ErrorApi(409, "CUENTA_NO_DISPONIBLE", "No fue posible crear la cuenta.") from error

    if datos.roles:
        roles_unicos = set(datos.roles)
        for rol in roles_unicos:
            sesion_db.add(
                UsuarioRol(
                    usuario_id=usuario.id,
                    rol=rol,
                    asignado_en=instante,
                    asignado_por_id=actor_id,
                )
            )

    auditar(
        sesion_db,
        accion="usuario.crear",
        entidad="usuario",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=usuario.id,
        direccion_ip=direccion_ip,
        contexto={"roles": [r.value for r in datos.roles]} if datos.roles else None,
    )
    sesion_db.commit()
    sesion_db.refresh(usuario)
    return usuario


def asignar_roles_usuario(
    sesion_db: Session,
    usuario: Usuario,
    nuevos_roles: list[RolUsuario],
    *,
    actor_id: uuid.UUID,
    direccion_ip: str | None,
) -> Usuario:
    instante = ahora_utc()
    roles_unicos = set(nuevos_roles)

    # Eliminar roles actuales y asignar los nuevos
    sesion_db.scalars(select(UsuarioRol).where(UsuarioRol.usuario_id == usuario.id)).all()
    for rol_existente in list(usuario.roles):
        sesion_db.delete(rol_existente)

    for rol in roles_unicos:
        sesion_db.add(
            UsuarioRol(
                usuario_id=usuario.id,
                rol=rol,
                asignado_en=instante,
                asignado_por_id=actor_id,
            )
        )

    usuario.actualizado_en = instante
    auditar(
        sesion_db,
        accion="usuario.asignar_roles",
        entidad="usuario",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=usuario.id,
        direccion_ip=direccion_ip,
        contexto={"roles": [r.value for r in roles_unicos]},
    )
    sesion_db.commit()
    sesion_db.refresh(usuario)
    return usuario


def autenticar(
    sesion_db: Session,
    correo: str,
    contrasena: str,
    ajustes: Ajustes,
    *,
    direccion_ip: str | None,
    agente_usuario: str | None,
) -> tuple[str, Sesion]:
    instante = ahora_utc()
    usuario = sesion_db.scalar(select(Usuario).where(Usuario.correo == normalizar_correo(correo)))

    contrasena_valida = verificar_contrasena(
        usuario.contrasena_hash if usuario else _hash_ficticio,
        contrasena,
    )
    acceso_valido = bool(
        usuario
        and usuario.activo
        and not (usuario.bloqueado_hasta and usuario.bloqueado_hasta > instante)
        and contrasena_valida
    )
    if not acceso_valido:
        if usuario and usuario.activo:
            usuario.intentos_fallidos += 1
            if usuario.intentos_fallidos >= ajustes.maximo_intentos_fallidos:
                usuario.bloqueado_hasta = instante + timedelta(minutes=ajustes.bloqueo_minutos)
                usuario.intentos_fallidos = 0
            usuario.actualizado_en = instante
            auditar(
                sesion_db,
                accion="sesion.ingreso",
                entidad="usuario",
                resultado="denegado",
                usuario_id=usuario.id,
                entidad_id=usuario.id,
                direccion_ip=direccion_ip,
            )
            sesion_db.commit()
        raise ErrorApi(401, "CREDENCIALES_INVALIDAS", "Las credenciales no son válidas.")

    assert usuario is not None
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_acceso = instante
    usuario.actualizado_en = instante
    token, token_hash = crear_token()
    sesion = Sesion(
        usuario_id=usuario.id,
        token_hash=token_hash,
        creada_en=instante,
        expira_en=instante + timedelta(minutes=ajustes.duracion_sesion_minutos),
        ultimo_uso_en=instante,
        direccion_ip=direccion_ip,
        agente_usuario=agente_usuario[:512] if agente_usuario else None,
    )
    sesion_db.add(sesion)
    auditar(
        sesion_db,
        accion="sesion.ingreso",
        entidad="sesion",
        resultado="exito",
        usuario_id=usuario.id,
        direccion_ip=direccion_ip,
    )
    sesion_db.commit()
    sesion_db.refresh(sesion)
    return token, sesion


def obtener_sesion_activa(sesion_db: Session, token: str) -> Sesion:
    instante = ahora_utc()
    sesion = sesion_db.scalar(select(Sesion).where(Sesion.token_hash == hash_token(token)))
    if (
        not sesion
        or sesion.revocada_en is not None
        or sesion.expira_en <= instante
        or not sesion.usuario.activo
    ):
        raise ErrorApi(401, "SESION_INVALIDA", "La sesión no es válida o expiró.")
    sesion.ultimo_uso_en = instante
    sesion_db.commit()
    return sesion


def revocar_sesion(sesion_db: Session, sesion: Sesion, *, actor_id: uuid.UUID) -> None:
    if sesion.revocada_en is None:
        sesion.revocada_en = ahora_utc()
        auditar(
            sesion_db,
            accion="sesion.revocar",
            entidad="sesion",
            resultado="exito",
            usuario_id=actor_id,
            entidad_id=sesion.id,
        )
        sesion_db.commit()


def desactivar_usuario(
    sesion_db: Session,
    usuario: Usuario,
    *,
    activo: bool,
    actor_id: uuid.UUID,
    direccion_ip: str | None,
) -> Usuario:
    usuario.activo = activo
    usuario.actualizado_en = ahora_utc()
    if not activo:
        sesion_db.execute(
            update(Sesion)
            .where(Sesion.usuario_id == usuario.id, Sesion.revocada_en.is_(None))
            .values(revocada_en=ahora_utc())
        )
    auditar(
        sesion_db,
        accion="usuario.activar" if activo else "usuario.desactivar",
        entidad="usuario",
        resultado="exito",
        usuario_id=actor_id,
        entidad_id=usuario.id,
        direccion_ip=direccion_ip,
    )
    sesion_db.commit()
    sesion_db.refresh(usuario)
    return usuario
