from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.api.errores import ErrorApi
from app.base_datos.sesion import obtener_sesion
from app.dominios.autenticacion.modelos import Sesion, Usuario
from app.dominios.autenticacion.servicio import obtener_sesion_activa

portador = HTTPBearer(auto_error=False)
SesionDb = Annotated[Session, Depends(obtener_sesion)]


def sesion_actual(
    sesion_db: SesionDb,
    credenciales: Annotated[HTTPAuthorizationCredentials | None, Depends(portador)],
) -> Sesion:
    if not credenciales or credenciales.scheme.casefold() != "bearer":
        raise ErrorApi(401, "SESION_REQUERIDA", "Se requiere una sesión válida.")
    return obtener_sesion_activa(sesion_db, credenciales.credentials)


SesionActual = Annotated[Sesion, Depends(sesion_actual)]


def usuario_actual(sesion: SesionActual) -> Usuario:
    return sesion.usuario


UsuarioActual = Annotated[Usuario, Depends(usuario_actual)]


def administrador_actual(usuario: UsuarioActual) -> Usuario:
    if not usuario.es_administrador_sistema:
        raise ErrorApi(403, "PERMISO_DENEGADO", "No cuenta con permiso para esta acción.")
    return usuario


AdministradorActual = Annotated[Usuario, Depends(administrador_actual)]
