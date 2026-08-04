import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.dominios.cupos.modelos import EstadoCupoDemo


class CrearCupoDemo(BaseModel):
    estudio_id: uuid.UUID
    fuente: str = Field(min_length=2, max_length=180)
    dias_validez: int = Field(default=30, ge=15, le=90)
    motivo: str = Field(min_length=3, max_length=1000)


class CambiarCupoDemo(BaseModel):
    estado: EstadoCupoDemo
    motivo: str = Field(min_length=3, max_length=1000)
    paciente_id: uuid.UUID | None = None
    dias_validez: int | None = Field(default=None, ge=15, le=90)
    fuente: str | None = Field(default=None, min_length=2, max_length=180)


class HistorialCupoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    estado_anterior: str | None
    estado_nuevo: str
    paciente_id: uuid.UUID | None
    motivo: str
    autor_id: uuid.UUID | None
    fecha: datetime


class CupoDemoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    estudio_id: uuid.UUID
    paciente_id: uuid.UUID | None
    estado: EstadoCupoDemo
    fuente: str
    responsable_id: uuid.UUID | None
    dias_validez: int
    confirmado_en: datetime
    vence_en: datetime
    creado_en: datetime
    actualizado_en: datetime
    vencido: bool
    vence_pronto: bool
    historial: list[HistorialCupoRespuesta] = []
