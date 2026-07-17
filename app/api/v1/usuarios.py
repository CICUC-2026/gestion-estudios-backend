import uuid

from fastapi import APIRouter, Request
from sqlalchemy import select

from app.api.errores import ErrorApi
from app.dominios.autenticacion.dependencias import AdministradorActual, SesionDb
from app.dominios.autenticacion.esquemas import (
    CambiarEstadoUsuario,
    CrearUsuario,
    UsuarioRespuesta,
)
from app.dominios.autenticacion.modelos import Usuario
from app.dominios.autenticacion.servicio import crear_usuario, desactivar_usuario

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


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
    return UsuarioRespuesta.model_validate(usuario)


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
    return UsuarioRespuesta.model_validate(usuario)
