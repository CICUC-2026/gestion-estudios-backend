import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.dominios.operacion.modelos import EstadoTarea, PrioridadTarea


class CrearTarea(BaseModel):
    titulo: str = Field(min_length=1, max_length=160)
    descripcion: str | None = None
    prioridad: PrioridadTarea = PrioridadTarea.MEDIA
    vence_en: datetime | None = None
    responsable_id: uuid.UUID | None = None
    paciente_id: uuid.UUID | None = None
    estudio_id: uuid.UUID | None = None


class ActualizarTarea(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=160)
    descripcion: str | None = None
    prioridad: PrioridadTarea | None = None
    estado: EstadoTarea | None = None
    vence_en: datetime | None = None
    responsable_id: uuid.UUID | None = None
    paciente_id: uuid.UUID | None = None
    estudio_id: uuid.UUID | None = None


class TareaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    titulo: str
    descripcion: str | None
    prioridad: PrioridadTarea
    estado: EstadoTarea
    vence_en: datetime | None
    creada_por_id: uuid.UUID | None
    responsable_id: uuid.UUID | None
    paciente_id: uuid.UUID | None
    estudio_id: uuid.UUID | None
    creada_en: datetime
    actualizada_en: datetime


class CrearReporte(BaseModel):
    nombre: str = Field(min_length=1, max_length=160)
    finalidad: str = Field(min_length=1, max_length=240)
    fecha_corte: datetime | None = None
    estudio_id: uuid.UUID | None = None
    estados_tarea: list[EstadoTarea] = []


class ReporteRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    nombre: str
    finalidad: str
    fecha_corte: datetime
    contenido: dict[str, Any]
    creado_por_id: uuid.UUID | None
    creado_en: datetime
