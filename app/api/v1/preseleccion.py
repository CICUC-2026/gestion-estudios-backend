import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.dominios.autenticacion.dependencias import SesionDb, UsuarioActual, requerir_roles
from app.dominios.autenticacion.modelos import RolUsuario, Usuario
from app.dominios.preseleccion.esquemas import (
    CambiarEstadoPreseleccionDemo,
    CrearPreseleccionDemo,
    EvaluarCriterioDemo,
    PreseleccionDemoRespuesta,
)
from app.dominios.preseleccion.modelos import PreseleccionDemo
from app.dominios.preseleccion.servicio import cambiar_estado, crear, evaluar, obtener

router = APIRouter(prefix="/preselecciones-demo", tags=["preselección demo"])
Revisor = Annotated[
    Usuario,
    Depends(requerir_roles(RolUsuario.MEDICO_INVESTIGADOR, RolUsuario.INVESTIGADOR_PRINCIPAL)),
]
Confirmador = Annotated[Usuario, Depends(requerir_roles(RolUsuario.INVESTIGADOR_PRINCIPAL))]


@router.get("", response_model=list[PreseleccionDemoRespuesta])
def listar(sesion: SesionDb, _: UsuarioActual) -> list[PreseleccionDemo]:
    return list(
        sesion.scalars(select(PreseleccionDemo).order_by(PreseleccionDemo.creada_en.desc()))
        .unique()
        .all()
    )


@router.post("", response_model=PreseleccionDemoRespuesta, status_code=201)
def registrar(datos: CrearPreseleccionDemo, sesion: SesionDb, usuario: Revisor) -> PreseleccionDemo:
    return crear(sesion, datos, usuario)


@router.get("/{identificador}", response_model=PreseleccionDemoRespuesta)
def detalle(identificador: uuid.UUID, sesion: SesionDb, _: UsuarioActual) -> PreseleccionDemo:
    return obtener(sesion, identificador)


@router.put("/{identificador}/criterios/{criterio_id}", response_model=PreseleccionDemoRespuesta)
def registrar_evaluacion(
    identificador: uuid.UUID,
    criterio_id: uuid.UUID,
    datos: EvaluarCriterioDemo,
    sesion: SesionDb,
    usuario: Revisor,
) -> PreseleccionDemo:
    return evaluar(sesion, obtener(sesion, identificador), criterio_id, datos, usuario)


@router.patch("/{identificador}/estado", response_model=PreseleccionDemoRespuesta)
def transicionar(
    identificador: uuid.UUID,
    datos: CambiarEstadoPreseleccionDemo,
    sesion: SesionDb,
    usuario: Confirmador,
) -> PreseleccionDemo:
    return cambiar_estado(sesion, obtener(sesion, identificador), datos, usuario)
