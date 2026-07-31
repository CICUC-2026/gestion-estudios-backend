import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base_datos.modelos import ModeloBase


class EstadoOperacionalEstudio(str, enum.Enum):
    ACTIVADO = "activado"
    CERRADO_TEMPORALMENTE = "cerrado_temporalmente"
    CERRADO_DEFINITIVO = "cerrado_definitivo"
    SUSPENDIDO = "suspendido"
    SIN_CONFIRMAR = "sin_confirmar"


class EstadoDisponibilidadEstudio(str, enum.Enum):
    CON_CUPO = "con_cupo"
    SIN_CUPO = "sin_cupo"
    LISTA_ESPERA = "lista_espera"
    SLOT_RESERVADO = "slot_reservado"
    SIN_CONFIRMAR = "sin_confirmar"


class EtiquetaVigencia(str, enum.Enum):
    VIGENTE = "vigente"
    POR_REVISAR = "por_revisar"
    DESACTUALIZADA = "desactualizada"


class AlcanceCriterio(str, enum.Enum):
    ESTUDIO = "estudio"
    COHORTE = "cohorte"
    BRAZO = "brazo"


class EstadoEstudio(str, enum.Enum):
    BORRADOR = "borrador"
    EN_REVISION = "en_revision"
    VIGENTE = "vigente"
    SUSPENDIDO = "suspendido"
    CERRADO = "cerrado"
    ARCHIVADO = "archivado"


class EstadoVersionProtocolo(str, enum.Enum):
    BORRADOR = "borrador"
    EN_REVISION = "en_revision"
    VIGENTE = "vigente"
    REEMPLAZADA = "reemplazada"
    ARCHIVADA = "archivada"


class TipoCriterio(str, enum.Enum):
    INCLUSION = "inclusion"
    EXCLUSION = "exclusion"


class Estudio(ModeloBase):
    __tablename__ = "estudios"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    codigo_interno: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    titulo: Mapped[str] = mapped_column(String(256))
    patrocinador: Mapped[str] = mapped_column(String(120))
    fase: Mapped[str] = mapped_column(String(64))
    patologia: Mapped[str] = mapped_column(String(120), index=True)
    escenario_clinico: Mapped[str] = mapped_column(String(120))
    linea_tratamiento: Mapped[str] = mapped_column(String(64))
    centro_atencion: Mapped[str] = mapped_column(String(120), default="CICUC Principal")

    # HU-030: Separar estado operacional y disponibilidad
    estado_operacional: Mapped[EstadoOperacionalEstudio] = mapped_column(
        Enum(EstadoOperacionalEstudio, name="estado_operacional_estudio_enum"),
        default=EstadoOperacionalEstudio.SIN_CONFIRMAR,
        index=True,
    )
    disponibilidad: Mapped[EstadoDisponibilidadEstudio] = mapped_column(
        Enum(EstadoDisponibilidadEstudio, name="estado_disponibilidad_estudio_enum"),
        default=EstadoDisponibilidadEstudio.SIN_CONFIRMAR,
        index=True,
    )

    # Compatibilidad previa
    estado: Mapped[EstadoEstudio] = mapped_column(
        Enum(EstadoEstudio, name="estado_estudio_enum"), default=EstadoEstudio.BORRADOR, index=True
    )
    disponible: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    # HU-032: Fuente, vigencia y verificación
    fuente_informacion: Mapped[str | None] = mapped_column(String(256))
    fecha_corte: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    verificado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    fecha_verificacion: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    proxima_revision: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    observaciones: Mapped[str | None] = mapped_column(Text)
    investigador_principal_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    coordinador_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    cohortes: Mapped[list["CohorteEstudio"]] = relationship(
        back_populates="estudio", cascade="all, delete-orphan"
    )
    versiones: Mapped[list["VersionProtocolo"]] = relationship(
        back_populates="estudio", cascade="all, delete-orphan"
    )
    historial_estados: Mapped[list["HistorialEstadoEstudio"]] = relationship(
        back_populates="estudio", cascade="all, delete-orphan"
    )

    @property
    def etiqueta_vigencia(self) -> EtiquetaVigencia:
        if not self.fecha_verificacion:
            return EtiquetaVigencia.POR_REVISAR
        ahora = datetime.now(UTC)
        if self.proxima_revision and ahora > self.proxima_revision:
            return EtiquetaVigencia.DESACTUALIZADA
        dias_desde_verificacion = (ahora - self.fecha_verificacion).days
        if dias_desde_verificacion > 30:
            return EtiquetaVigencia.POR_REVISAR
        return EtiquetaVigencia.VIGENTE


class CohorteEstudio(ModeloBase):
    __tablename__ = "cohortes_estudios"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    estudio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("estudios.id", ondelete="CASCADE"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(Text)
    patologia: Mapped[str | None] = mapped_column(String(120))
    subtipo_histologico: Mapped[str | None] = mapped_column(String(120))
    escenario_clinico: Mapped[str | None] = mapped_column(String(120))
    linea_tratamiento: Mapped[str | None] = mapped_column(String(64))
    biomarcadores_requeridos: Mapped[list[str]] = mapped_column(JSON, default=list)
    meta_reclutamiento: Mapped[int | None] = mapped_column(Integer)

    # HU-030/HU-031: Estado y disponibilidad especificos por cohorte
    estado_operacional: Mapped[EstadoOperacionalEstudio | None] = mapped_column(
        Enum(EstadoOperacionalEstudio, name="estado_operacional_cohorte_enum"), nullable=True
    )
    disponibilidad: Mapped[EstadoDisponibilidadEstudio | None] = mapped_column(
        Enum(EstadoDisponibilidadEstudio, name="estado_disponibilidad_cohorte_enum"), nullable=True
    )

    estudio: Mapped[Estudio] = relationship(back_populates="cohortes")
    brazos: Mapped[list["BrazoEstudio"]] = relationship(
        back_populates="cohorte", cascade="all, delete-orphan"
    )


class BrazoEstudio(ModeloBase):
    __tablename__ = "brazos_estudio"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cohorte_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cohortes_estudios.id", ondelete="CASCADE"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(Text)

    cohorte: Mapped[CohorteEstudio] = relationship(back_populates="brazos")


class HistorialEstadoEstudio(ModeloBase):
    __tablename__ = "historial_estados_estudio"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    estudio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("estudios.id", ondelete="CASCADE"), index=True
    )
    campo_modificado: Mapped[str] = mapped_column(String(64))
    valor_anterior: Mapped[str | None] = mapped_column(String(64))
    valor_nuevo: Mapped[str] = mapped_column(String(64))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    autor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    fuente: Mapped[str | None] = mapped_column(String(256))
    motivo: Mapped[str | None] = mapped_column(Text)

    estudio: Mapped[Estudio] = relationship(back_populates="historial_estados")


class VersionProtocolo(ModeloBase):
    __tablename__ = "versiones_protocolo"
    __table_args__ = (
        UniqueConstraint("estudio_id", "numero_version", name="uq_estudio_version_numero"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    estudio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("estudios.id", ondelete="CASCADE"), index=True
    )
    numero_version: Mapped[str] = mapped_column(String(32))
    descripcion_cambios: Mapped[str] = mapped_column(Text)
    estado: Mapped[EstadoVersionProtocolo] = mapped_column(
        Enum(EstadoVersionProtocolo, name="estado_version_protocolo_enum"),
        default=EstadoVersionProtocolo.BORRADOR,
        index=True,
    )
    es_vigente: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    creada_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    publicada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    publicada_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    estudio: Mapped[Estudio] = relationship(back_populates="versiones")
    criterios: Mapped[list["CriterioManual"]] = relationship(
        back_populates="version", cascade="all, delete-orphan"
    )


class CriterioManual(ModeloBase):
    __tablename__ = "criterios_manuales"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("versiones_protocolo.id", ondelete="CASCADE"), index=True
    )
    tipo: Mapped[TipoCriterio] = mapped_column(
        Enum(TipoCriterio, name="tipo_criterio_enum"), index=True
    )
    alcance: Mapped[AlcanceCriterio] = mapped_column(
        Enum(AlcanceCriterio, name="alcance_criterio_enum"),
        default=AlcanceCriterio.ESTUDIO,
        index=True,
    )
    cohorte_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cohortes_estudios.id", ondelete="SET NULL"), nullable=True
    )
    brazo_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("brazos_estudio.id", ondelete="SET NULL"), nullable=True
    )
    orden: Mapped[int] = mapped_column(Integer, default=1)
    codigo_criterio: Mapped[str] = mapped_column(String(32))
    descripcion: Mapped[str] = mapped_column(Text)
    seccion_fuente: Mapped[str | None] = mapped_column(String(120))
    observaciones: Mapped[str | None] = mapped_column(Text)

    version: Mapped[VersionProtocolo] = relationship(back_populates="criterios")
