import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.dominios.estudios.modelos import (
    AlcanceCriterio,
    EstadoDisponibilidadEstudio,
    EstadoEstudio,
    EstadoOperacionalEstudio,
    EstadoVersionProtocolo,
    EtiquetaVigencia,
    TipoCriterio,
)


class CrearBrazo(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None


class BrazoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    cohorte_id: uuid.UUID
    nombre: str
    descripcion: str | None


class CrearCohorte(BaseModel):
    nombre: str = Field(min_length=1, max_length=120)
    descripcion: str | None = None
    patologia: str | None = None
    subtipo_histologico: str | None = None
    escenario_clinico: str | None = None
    linea_tratamiento: str | None = None
    biomarcadores_requeridos: list[str] = Field(default_factory=list)
    meta_reclutamiento: int | None = Field(default=None, ge=1)
    estado_operacional: EstadoOperacionalEstudio | None = None
    disponibilidad: EstadoDisponibilidadEstudio | None = None
    brazos: list[CrearBrazo] = Field(default_factory=list)


class CohorteRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    estudio_id: uuid.UUID
    nombre: str
    descripcion: str | None
    patologia: str | None
    subtipo_histologico: str | None
    escenario_clinico: str | None
    linea_tratamiento: str | None
    biomarcadores_requeridos: list[str]
    meta_reclutamiento: int | None
    estado_operacional: EstadoOperacionalEstudio | None
    disponibilidad: EstadoDisponibilidadEstudio | None
    brazos: list[BrazoRespuesta] = Field(default_factory=list)


class CrearCriterioManual(BaseModel):
    tipo: TipoCriterio
    codigo_criterio: str = Field(min_length=1, max_length=32)
    descripcion: str = Field(min_length=1)
    orden: int = Field(default=1, ge=1)
    alcance: AlcanceCriterio = Field(default=AlcanceCriterio.ESTUDIO)
    cohorte_id: uuid.UUID | None = None
    brazo_id: uuid.UUID | None = None
    seccion_fuente: str | None = None
    observaciones: str | None = None


class CriterioManualRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    version_id: uuid.UUID
    tipo: TipoCriterio
    alcance: AlcanceCriterio
    cohorte_id: uuid.UUID | None
    brazo_id: uuid.UUID | None
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


class ActualizarEstadoOperacional(BaseModel):
    estado_operacional: EstadoOperacionalEstudio
    fuente: str = Field(min_length=1, max_length=256)
    motivo: str = Field(min_length=1)


class ActualizarDisponibilidad(BaseModel):
    disponibilidad: EstadoDisponibilidadEstudio
    fuente: str = Field(min_length=1, max_length=256)
    motivo: str = Field(min_length=1)


class ReconfirmarVigencia(BaseModel):
    fuente_informacion: str = Field(min_length=1, max_length=256)
    fecha_corte: datetime | None = None
    dias_validez: int = Field(default=30, ge=1, le=365)


class HistorialEstadoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    estudio_id: uuid.UUID
    campo_modificado: str
    valor_anterior: str | None
    valor_nuevo: str
    fecha: datetime
    autor_id: uuid.UUID | None
    fuente: str | None
    motivo: str | None


class CrearEstudio(BaseModel):
    codigo_interno: str = Field(min_length=1, max_length=64)
    titulo: str = Field(min_length=1, max_length=256)
    patrocinador: str = Field(min_length=1, max_length=120)
    fase: str = Field(min_length=1, max_length=64)
    patologia: str = Field(min_length=1, max_length=120)
    escenario_clinico: str = Field(min_length=1, max_length=120)
    linea_tratamiento: str = Field(min_length=1, max_length=64)
    centro_atencion: str = Field(default="CICUC Principal", max_length=120)
    estado_operacional: EstadoOperacionalEstudio = Field(
        default=EstadoOperacionalEstudio.SIN_CONFIRMAR
    )
    disponibilidad: EstadoDisponibilidadEstudio = Field(
        default=EstadoDisponibilidadEstudio.SIN_CONFIRMAR
    )
    fuente_informacion: str | None = None
    fecha_corte: datetime | None = None
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
    estado_operacional: EstadoOperacionalEstudio | None = None
    disponibilidad: EstadoDisponibilidadEstudio | None = None
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
    estado_operacional: EstadoOperacionalEstudio
    disponibilidad: EstadoDisponibilidadEstudio
    estado: EstadoEstudio
    disponible: bool
    fuente_informacion: str | None
    fecha_corte: datetime | None
    verificado_por_id: uuid.UUID | None
    fecha_verificacion: datetime | None
    proxima_revision: datetime | None
    etiqueta_vigencia: EtiquetaVigencia
    observaciones: str | None
    investigador_principal_id: uuid.UUID | None
    coordinador_id: uuid.UUID | None
    creado_en: datetime
    actualizado_en: datetime
    cohortes: list[CohorteRespuesta] = Field(default_factory=list)
    version_vigente: VersionProtocoloRespuesta | None = None
    historial_estados: list[HistorialEstadoRespuesta] = Field(default_factory=list)


class ComparacionVersionesRespuesta(BaseModel):
    estudio_id: uuid.UUID
    version_anterior: VersionProtocoloRespuesta
    version_nueva: VersionProtocoloRespuesta
    criterios_agregados: list[CriterioManualRespuesta]
    criterios_eliminados: list[CriterioManualRespuesta]
    criterios_modificados: list[dict[str, CriterioManualRespuesta]]
