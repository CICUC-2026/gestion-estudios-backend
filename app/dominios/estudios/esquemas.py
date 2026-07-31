import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.dominios.estudios.modelos import (
    EstadoEstudio,
    EstadoVersionProtocolo,
    TipoCriterio,
)


class CrearCohorte(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None
    biomarcadores_requeridos: list[str] = Field(default_factory=list)
    meta_reclutamiento: int | None = Field(default=None, ge=1)


class CohorteRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    estudio_id: uuid.UUID
    nombre: str
    descripcion: str | None
    biomarcadores_requeridos: list[str]
    meta_reclutamiento: int | None


class CrearCriterioManual(BaseModel):
    tipo: TipoCriterio
    codigo_criterio: str = Field(min_length=1, max_length=32)
    descripcion: str = Field(min_length=1)
    orden: int = Field(default=1, ge=1)
    seccion_fuente: str | None = None
    observaciones: str | None = None


class CriterioManualRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_id: uuid.UUID
    tipo: TipoCriterio
    orden: int
    codigo_criterio: str
    descripcion: str
    seccion_fuente: str | None
    observaciones: str | None


class CrearVersionProtocolo(BaseModel):
    numero_version: str = Field(min_length=1, max_length=32)
    descripcion_cambios: str = Field(min_length=1)
    criterios: list[CrearCriterioManual] = Field(default_factory=list)


class VersionProtocoloRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    estudio_id: uuid.UUID
    numero_version: str
    descripcion_cambios: str
    estado: EstadoVersionProtocolo
    es_vigente: bool
    creada_en: datetime
    creada_por_id: uuid.UUID | None
    publicada_en: datetime | None
    publicada_por_id: uuid.UUID | None
    criterios: list[CriterioManualRespuesta] = Field(default_factory=list)


class CrearEstudio(BaseModel):
    codigo_interno: str = Field(min_length=1, max_length=64)
    titulo: str = Field(min_length=1, max_length=256)
    patrocinador: str = Field(min_length=1, max_length=120)
    fase: str = Field(min_length=1, max_length=64)
    patologia: str = Field(min_length=1, max_length=120)
    escenario_clinico: str = Field(min_length=1, max_length=120)
    linea_tratamiento: str = Field(min_length=1, max_length=64)
    centro_atencion: str = Field(default="CICUC Principal", max_length=120)
    observaciones: str | None = None
    investigador_principal_id: uuid.UUID | None = None
    coordinador_id: uuid.UUID | None = None
    cohortes: list[CrearCohorte] = Field(default_factory=list)


class ActualizarEstudio(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=256)
    patrocinador: str | None = Field(default=None, min_length=1, max_length=120)
    fase: str | None = Field(default=None, min_length=1, max_length=64)
    patologia: str | None = Field(default=None, min_length=1, max_length=120)
    escenario_clinico: str | None = Field(default=None, min_length=1, max_length=120)
    linea_tratamiento: str | None = Field(default=None, min_length=1, max_length=64)
    centro_atencion: str | None = Field(default=None, max_length=120)
    estado: EstadoEstudio | None = None
    disponible: bool | None = None
    observaciones: str | None = None
    investigador_principal_id: uuid.UUID | None = None
    coordinador_id: uuid.UUID | None = None


class EstudioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    codigo_interno: str
    titulo: str
    patrocinador: str
    fase: str
    patologia: str
    escenario_clinico: str
    linea_tratamiento: str
    centro_atencion: str
    estado: EstadoEstudio
    disponible: bool
    observaciones: str | None
    investigador_principal_id: uuid.UUID | None
    coordinador_id: uuid.UUID | None
    creado_en: datetime
    actualizado_en: datetime
    cohortes: list[CohorteRespuesta] = Field(default_factory=list)
    version_vigente: VersionProtocoloRespuesta | None = None


class ComparacionVersionesRespuesta(BaseModel):
    estudio_id: uuid.UUID
    version_anterior: VersionProtocoloRespuesta
    version_nueva: VersionProtocoloRespuesta
    criterios_agregados: list[CriterioManualRespuesta]
    criterios_eliminados: list[CriterioManualRespuesta]
    criterios_modificados: list[dict[str, CriterioManualRespuesta]]
