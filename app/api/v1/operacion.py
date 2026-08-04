import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.api.errores import ErrorApi
from app.dominios.autenticacion.dependencias import SesionDb, UsuarioActual, requerir_roles
from app.dominios.autenticacion.modelos import RolUsuario, Usuario
from app.dominios.operacion.esquemas import (
    ActualizarTarea,
    CrearReporte,
    CrearTarea,
    ReporteRespuesta,
    TareaRespuesta,
)
from app.dominios.operacion.modelos import ReporteOperativo, Tarea
from app.dominios.operacion.servicio import actualizar_tarea, crear_tarea, preparar_reporte

router = APIRouter(tags=["operación"])
GestionOperativa = Annotated[
    Usuario,
    Depends(
        requerir_roles(
            RolUsuario.COORDINADOR, RolUsuario.ENFERMERIA, RolUsuario.INVESTIGADOR_PRINCIPAL
        )
    ),
]
Reportero = Annotated[
    Usuario,
    Depends(requerir_roles(RolUsuario.COORDINADOR, RolUsuario.INVESTIGADOR_PRINCIPAL)),
]


@router.get("/tareas", response_model=list[TareaRespuesta])
def listar_tareas(sesion: SesionDb, _: UsuarioActual) -> list[Tarea]:
    return list(sesion.scalars(select(Tarea).order_by(Tarea.creada_en.desc())).all())


@router.post("/tareas", response_model=TareaRespuesta, status_code=201)
def registrar_tarea(datos: CrearTarea, sesion: SesionDb, usuario: GestionOperativa) -> Tarea:
    return crear_tarea(sesion, datos, usuario)


@router.patch("/tareas/{tarea_id}", response_model=TareaRespuesta)
def modificar_tarea(
    tarea_id: uuid.UUID, datos: ActualizarTarea, sesion: SesionDb, usuario: GestionOperativa
) -> Tarea:
    tarea = sesion.get(Tarea, tarea_id)
    if not tarea:
        raise ErrorApi(404, "RECURSO_NO_ENCONTRADO", "No se encontró la tarea.")
    return actualizar_tarea(sesion, tarea, datos, usuario)


@router.get("/reportes", response_model=list[ReporteRespuesta])
def listar_reportes(sesion: SesionDb, _: UsuarioActual) -> list[ReporteOperativo]:
    return list(
        sesion.scalars(select(ReporteOperativo).order_by(ReporteOperativo.creado_en.desc())).all()
    )


@router.post("/reportes", response_model=ReporteRespuesta, status_code=201)
def registrar_reporte(
    datos: CrearReporte, sesion: SesionDb, usuario: Reportero
) -> ReporteOperativo:
    return preparar_reporte(sesion, datos, usuario)
