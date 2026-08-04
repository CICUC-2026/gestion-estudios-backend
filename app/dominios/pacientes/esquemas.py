import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.dominios.pacientes.modelos import EstadoPacienteDemo


class CrearPacienteDemo(BaseModel):
    codigo: str = Field(min_length=9, max_length=40)
    rango_etario: str = Field(min_length=3, max_length=40)
    patologia: str = Field(min_length=2, max_length=160)
    estado: EstadoPacienteDemo = EstadoPacienteDemo.ANTECEDENTES_PENDIENTES

    @field_validator("codigo")
    @classmethod
    def validar_codigo_demo(cls, valor: str) -> str:
        normalizado = valor.strip().upper()
        if not normalizado.startswith("PX-DEMO-"):
            raise ValueError("Solo se permiten códigos sintéticos PX-DEMO-.")
        return normalizado


class ActualizarPacienteDemo(BaseModel):
    rango_etario: str | None = Field(default=None, min_length=3, max_length=40)
    patologia: str | None = Field(default=None, min_length=2, max_length=160)
    estado: EstadoPacienteDemo | None = None
    archivado: bool | None = None


class PacienteDemoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    codigo: str
    rango_etario: str
    patologia: str
    estado: EstadoPacienteDemo
    sintetico: bool
    archivado: bool
    creado_en: datetime
    actualizado_en: datetime


class CrearDiagnosticoDemo(BaseModel):
    diagnostico: str = Field(min_length=2, max_length=180)
    biomarcador: str | None = Field(default=None, max_length=120)
    resultado_biomarcador: str | None = Field(default=None, max_length=120)
    fecha: date
    fuente: str = Field(min_length=2, max_length=160)


class DiagnosticoDemoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    paciente_id: uuid.UUID
    diagnostico: str
    biomarcador: str | None
    resultado_biomarcador: str | None
    fecha: date
    fuente: str
    creado_en: datetime


class AsociarEstudioDemo(BaseModel):
    estudio_id: uuid.UUID
    observaciones: str | None = Field(default=None, max_length=1000)


class PacienteEstudioDemoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    paciente_id: uuid.UUID
    estudio_id: uuid.UUID
    estado: str
    observaciones: str | None
    creado_en: datetime
