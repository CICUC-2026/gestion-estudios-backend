import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.dominios.exportaciones.modelos import FormatoExportacion

ENTIDADES_PERMITIDAS = {
    "pacientes",
    "diagnosticos",
    "estudios",
    "asociaciones",
    "tareas",
    "preselecciones",
    "cupos",
}


class CrearExportacionDemo(BaseModel):
    finalidad: str = Field(min_length=3, max_length=240)
    formato: FormatoExportacion
    entidades: list[str] = Field(default_factory=lambda: sorted(ENTIDADES_PERMITIDAS))
    estudio_id: uuid.UUID | None = None


class ExportacionDemoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    finalidad: str
    formato: FormatoExportacion
    filtros: dict[str, Any]
    campos: list[str]
    cantidad: int
    hash_sha256: str
    autor_id: uuid.UUID | None
    creada_en: datetime
