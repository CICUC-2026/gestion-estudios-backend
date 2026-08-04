import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from app.dominios.autenticacion.dependencias import SesionDb, UsuarioActual, requerir_roles
from app.dominios.autenticacion.modelos import RolUsuario, Usuario
from app.dominios.cupos.esquemas import CambiarCupoDemo, CrearCupoDemo, CupoDemoRespuesta
from app.dominios.cupos.modelos import CupoDemo
from app.dominios.cupos.servicio import cambiar, crear, listar, obtener

router = APIRouter(prefix="/cupos-demo", tags=["cupos demo"])
GestorCupo = Annotated[
    Usuario,
    Depends(requerir_roles(RolUsuario.ENFERMERIA, RolUsuario.COORDINADOR)),
]


@router.get("", response_model=list[CupoDemoRespuesta])
def listar_cupos(sesion: SesionDb, _: UsuarioActual) -> list[CupoDemo]:
    return listar(sesion)


@router.post("", response_model=CupoDemoRespuesta, status_code=201)
def confirmar(datos: CrearCupoDemo, sesion: SesionDb, usuario: GestorCupo) -> CupoDemo:
    return crear(sesion, datos, usuario)


@router.get("/{identificador}", response_model=CupoDemoRespuesta)
def detalle(identificador: uuid.UUID, sesion: SesionDb, _: UsuarioActual) -> CupoDemo:
    return obtener(sesion, identificador)


@router.patch("/{identificador}", response_model=CupoDemoRespuesta)
def transicionar(
    identificador: uuid.UUID, datos: CambiarCupoDemo, sesion: SesionDb, usuario: GestorCupo
) -> CupoDemo:
    return cambiar(sesion, obtener(sesion, identificador), datos, usuario)
