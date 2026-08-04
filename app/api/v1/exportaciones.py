from fastapi import APIRouter, Response
from sqlalchemy import select

from app.dominios.autenticacion.dependencias import AdministradorActual, SesionDb
from app.dominios.exportaciones.esquemas import CrearExportacionDemo, ExportacionDemoRespuesta
from app.dominios.exportaciones.modelos import ExportacionDemo
from app.dominios.exportaciones.servicio import generar

router = APIRouter(prefix="/exportaciones-demo", tags=["exportaciones demo"])


@router.get("", response_model=list[ExportacionDemoRespuesta])
def listar(sesion: SesionDb, _: AdministradorActual) -> list[ExportacionDemo]:
    return list(sesion.scalars(select(ExportacionDemo).order_by(ExportacionDemo.creada_en.desc())))


@router.post("")
def descargar(
    datos: CrearExportacionDemo, sesion: SesionDb, usuario: AdministradorActual
) -> Response:
    registro, archivo, tipo = generar(sesion, datos, usuario)
    return Response(
        archivo,
        media_type=tipo,
        headers={
            "Content-Disposition": (  # noqa: E501
                f'attachment; filename="cicuc-demo-{registro.id}.{datos.formato.value}"'
            ),
            "X-Exportacion-Id": str(registro.id),
            "X-Contenido-SHA256": registro.hash_sha256,
            "Cache-Control": "private, no-store, max-age=0",
        },
    )
