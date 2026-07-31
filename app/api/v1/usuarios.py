import uuid

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.errores import ErrorApi
from app.dominios.autenticacion.dependencias import AdministradorActual, SesionDb
from app.dominios.autenticacion.esquemas import (
    AsignarRolesUsuario,
    CambiarEstadoUsuario,
    CrearUsuario,
    UsuarioRespuesta,
)
from app.dominios.autenticacion.modelos import RolUsuario, Usuario
from app.dominios.autenticacion.servicio import (
    asignar_roles_usuario,
    crear_usuario,
    desactivar_usuario,
)

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def _serializar_usuario(usuario: Usuario) -> UsuarioRespuesta:
    roles_enum = [RolUsuario(r.rol) for r in usuario.roles]
    return UsuarioRespuesta(
        id=usuario.id,
        nombres=usuario.nombres,
        apellidos=usuario.apellidos,
        correo=usuario.correo,
        es_administrador_sistema=usuario.es_administrador_sistema,
        activo=usuario.activo,
        roles=roles_enum,
        ultimo_acceso=usuario.ultimo_acceso,
        creado_en=usuario.creado_en,
    )


@router.get("", response_model=list[UsuarioRespuesta])
def listar_usuarios(
    sesion_db: SesionDb,
    administrador: AdministradorActual,
) -> list[UsuarioRespuesta]:
    usuarios = sesion_db.scalars(select(Usuario).order_by(Usuario.creado_en.desc())).all()
    return [_serializar_usuario(u) for u in usuarios]


@router.post("", response_model=UsuarioRespuesta, status_code=201)
def registrar_usuario(
    datos: CrearUsuario,
    request: Request,
    sesion_db: SesionDb,
    administrador: AdministradorActual,
) -> UsuarioRespuesta:
    usuario = crear_usuario(
        sesion_db,
        datos,
        actor_id=administrador.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return _serializar_usuario(usuario)


@router.put("/{usuario_id}/roles", response_model=UsuarioRespuesta)
def actualizar_roles(
    usuario_id: uuid.UUID,
    datos: AsignarRolesUsuario,
    request: Request,
    sesion_db: SesionDb,
    administrador: AdministradorActual,
) -> UsuarioRespuesta:
    usuario = sesion_db.scalar(select(Usuario).where(Usuario.id == usuario_id))
    if not usuario:
        raise ErrorApi(404, "RECURSO_NO_ENCONTRADO", "No se encontró el usuario.")
    usuario = asignar_roles_usuario(
        sesion_db,
        usuario,
        datos.roles,
        actor_id=administrador.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return _serializar_usuario(usuario)


@router.patch("/{usuario_id}/estado", response_model=UsuarioRespuesta)
def actualizar_estado(
    usuario_id: uuid.UUID,
    datos: CambiarEstadoUsuario,
    request: Request,
    sesion_db: SesionDb,
    administrador: AdministradorActual,
) -> UsuarioRespuesta:
    usuario = sesion_db.scalar(select(Usuario).where(Usuario.id == usuario_id))
    if not usuario:
        raise ErrorApi(404, "RECURSO_NO_ENCONTRADO", "No se encontró el usuario.")
    if usuario.id == administrador.id and not datos.activo:
        raise ErrorApi(409, "OPERACION_NO_PERMITIDA", "No puede desactivar su propia cuenta.")
    usuario = desactivar_usuario(
        sesion_db,
        usuario,
        activo=datos.activo,
        actor_id=administrador.id,
        direccion_ip=request.client.host if request.client else None,
    )
    return _serializar_usuario(usuario)
