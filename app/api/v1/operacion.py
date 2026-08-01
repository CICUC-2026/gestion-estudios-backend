from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.dominios.autenticacion.dependencias import SesionDb, UsuarioActual, requerir_roles
from app.dominios.autenticacion.modelos import RolUsuario, Usuario
from app.dominios.operacion.esquemas import (
    CrearReporte,
    CrearTarea,
    ReporteRespuesta,
    TareaRespuesta,
)
from app.dominios.operacion.modelos import ReporteOperativo, Tarea
from app.dominios.operacion.servicio import crear_tarea, preparar_reporte

router = APIRouter(tags=["operación"])
GestionOperativa = Annotated[
    Usuario,
    Depends(
        requerir_roles(
            RolUsuario.COORDINADOR, RolUsuario.ENFERMERIA, RolUsuario.INVESTIGADOR_PRINCIPAL
        )
    ),
]


@router.get("/tareas", response_model=list[TareaRespuesta])
def listar_tareas(sesion: SesionDb, _: UsuarioActual) -> list[Tarea]:
    return list(sesion.scalars(select(Tarea).order_by(Tarea.creada_en.desc())).all())


@router.post("/tareas", response_model=TareaRespuesta, status_code=201)
def registrar_tarea(datos: CrearTarea, sesion: SesionDb, usuario: GestionOperativa) -> Tarea:
    return crear_tarea(sesion, datos, usuario)


@router.get("/reportes", response_model=list[ReporteRespuesta])
def listar_reportes(sesion: SesionDb, _: UsuarioActual) -> list[ReporteOperativo]:
    return list(
        sesion.scalars(select(ReporteOperativo).order_by(ReporteOperativo.creado_en.desc())).all()
    )


@router.post("/reportes", response_model=ReporteRespuesta, status_code=201)
def registrar_reporte(
    datos: CrearReporte, sesion: SesionDb, usuario: GestionOperativa
) -> ReporteOperativo:
    return preparar_reporte(sesion, datos, usuario)
