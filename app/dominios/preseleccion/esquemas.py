import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.dominios.preseleccion.modelos import EstadoEvaluacionDemo, EstadoPreseleccionDemo


class CrearPreseleccionDemo(BaseModel):
    paciente_id: uuid.UUID
    estudio_id: uuid.UUID
    version_id: uuid.UUID
    motivo: str = Field(min_length=3, max_length=500)


class EvaluarCriterioDemo(BaseModel):
    estado: EstadoEvaluacionDemo
    comentario: str = Field(min_length=2, max_length=2000)
    fuente: str = Field(min_length=2, max_length=180)


class CambiarEstadoPreseleccionDemo(BaseModel):
    estado: EstadoPreseleccionDemo
    motivo: str = Field(min_length=3, max_length=1000)
    resumen: str | None = Field(default=None, max_length=4000)


class EvaluacionDemoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    criterio_id: uuid.UUID
    estado: EstadoEvaluacionDemo
    comentario: str
    fuente: str
    autor_id: uuid.UUID | None
    actualizada_en: datetime


class HistorialDemoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    estado_anterior: str | None
    estado_nuevo: str
    motivo: str
    autor_id: uuid.UUID | None
    fecha: datetime


class PreseleccionDemoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    paciente_id: uuid.UUID
    estudio_id: uuid.UUID
    version_id: uuid.UUID
    estado: EstadoPreseleccionDemo
    resumen: str | None
    creada_por_id: uuid.UUID | None
    creada_en: datetime
    actualizada_en: datetime
    evaluaciones: list[EvaluacionDemoRespuesta] = []
    historial: list[HistorialDemoRespuesta] = []
