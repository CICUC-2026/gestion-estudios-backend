import uuid

from fastapi import APIRouter, Request, Response, status
from sqlalchemy import select

from app.api.errores import ErrorApi
from app.configuracion.ajustes import obtener_ajustes
from app.dominios.autenticacion.dependencias import SesionActual, SesionDb, UsuarioActual
from app.dominios.autenticacion.esquemas import (
    CambiarContrasena,
    CredencialesIngreso,
    SesionRespuesta,
    TokenSesion,
    UsuarioRespuesta,
)
from app.dominios.autenticacion.modelos import RolUsuario, Sesion
from app.dominios.autenticacion.servicio import (
    ahora_utc,
    auditar,
    autenticar,
    crear_hash_contrasena,
    revocar_sesion,
    verificar_contrasena,
)

router = APIRouter(prefix="/autenticacion", tags=["autenticación"])


@router.post("/ingresar", response_model=TokenSesion)
def ingresar(datos: CredencialesIngreso, request: Request, sesion_db: SesionDb) -> TokenSesion:
    token, sesion = autenticar(
        sesion_db,
        str(datos.correo),
        datos.contrasena,
        obtener_ajustes(),
        direccion_ip=request.client.host if request.client else None,
        agente_usuario=request.headers.get("user-agent"),
    )
    return TokenSesion(token_acceso=token, expira_en=sesion.expira_en)


@router.get("/yo", response_model=UsuarioRespuesta)
def yo(usuario: UsuarioActual) -> UsuarioRespuesta:
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


@router.post("/salir", status_code=status.HTTP_204_NO_CONTENT)
def salir(sesion_db: SesionDb, sesion: SesionActual) -> Response:
    revocar_sesion(sesion_db, sesion, actor_id=sesion.usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/sesiones", response_model=list[SesionRespuesta])
def listar_sesiones(sesion_db: SesionDb, sesion_actual: SesionActual) -> list[SesionRespuesta]:
    sesiones = sesion_db.scalars(
        select(Sesion)
        .where(Sesion.usuario_id == sesion_actual.usuario_id)
        .order_by(Sesion.creada_en.desc())
    ).all()
    return [
        SesionRespuesta.model_validate(sesion).model_copy(
            update={"es_actual": sesion.id == sesion_actual.id}
        )
        for sesion in sesiones
    ]


@router.delete("/sesiones/{sesion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_sesion(
    sesion_id: uuid.UUID,
    sesion_db: SesionDb,
    sesion_actual: SesionActual,
) -> Response:
    sesion = sesion_db.scalar(
        select(Sesion).where(
            Sesion.id == sesion_id,
            Sesion.usuario_id == sesion_actual.usuario_id,
        )
    )
    if not sesion:
        raise ErrorApi(404, "RECURSO_NO_ENCONTRADO", "No se encontró la sesión.")
    revocar_sesion(sesion_db, sesion, actor_id=sesion_actual.usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/cambiar-contrasena", status_code=status.HTTP_204_NO_CONTENT)
def cambiar_contrasena(
    datos: CambiarContrasena,
    sesion_db: SesionDb,
    sesion_actual: SesionActual,
) -> Response:
    usuario = sesion_actual.usuario
    if not verificar_contrasena(usuario.contrasena_hash, datos.contrasena_actual):
        raise ErrorApi(400, "CONTRASENA_ACTUAL_INVALIDA", "No fue posible cambiar la contraseña.")
    usuario.contrasena_hash = crear_hash_contrasena(datos.contrasena_nueva)
    usuario.actualizado_en = ahora_utc()
    otras_sesiones = sesion_db.scalars(
        select(Sesion).where(
            Sesion.usuario_id == usuario.id,
            Sesion.id != sesion_actual.id,
            Sesion.revocada_en.is_(None),
        )
    ).all()
    for otra in otras_sesiones:
        otra.revocada_en = ahora_utc()
    auditar(
        sesion_db,
        accion="usuario.cambiar_contrasena",
        entidad="usuario",
        resultado="exito",
        usuario_id=usuario.id,
        entidad_id=usuario.id,
    )
    sesion_db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
