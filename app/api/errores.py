from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel


class DetalleError(BaseModel):
    codigo: str
    mensaje: str
    detalles: dict[str, Any] | None = None


class ErrorApi(Exception):
    def __init__(self, estado: int, codigo: str, mensaje: str) -> None:
        self.estado = estado
        self.detalle = DetalleError(codigo=codigo, mensaje=mensaje)
        super().__init__(mensaje)


async def manejar_error_api(_: Request, error: ErrorApi) -> JSONResponse:
    return JSONResponse(
        status_code=error.estado,
        content={"error": error.detalle.model_dump(mode="json", exclude_none=True)},
    )
