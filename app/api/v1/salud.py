from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class EstadoSalud(BaseModel):
    estado: Literal["ok"]
    servicio: str


@router.get("/salud", response_model=EstadoSalud)
def consultar_salud() -> EstadoSalud:
    """Informa disponibilidad del proceso sin exponer configuración o datos."""
    return EstadoSalud(estado="ok", servicio="gestion-estudios-backend")
