from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.errores import ErrorApi, manejar_error_api
from app.api.v1.router import router as api_v1_router
from app.configuracion.ajustes import obtener_ajustes


@asynccontextmanager
async def ciclo_de_vida(_: FastAPI) -> AsyncIterator[None]:
    """Inicializa dependencias de aplicación sin conectarse implícitamente a datos."""
    obtener_ajustes()
    yield


def crear_aplicacion() -> FastAPI:
    ajustes = obtener_ajustes()
    aplicacion = FastAPI(
        title=ajustes.nombre_aplicacion,
        version="0.1.0",
        docs_url="/documentacion-api",
        openapi_url="/api/v1/openapi.json",
        lifespan=ciclo_de_vida,
    )
    aplicacion.add_middleware(
        CORSMiddleware,
        allow_origins=ajustes.lista_origenes_frontend,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    aplicacion.include_router(api_v1_router, prefix="/api/v1")
    aplicacion.add_exception_handler(ErrorApi, manejar_error_api)  # type: ignore[arg-type]
    return aplicacion


app = crear_aplicacion()
