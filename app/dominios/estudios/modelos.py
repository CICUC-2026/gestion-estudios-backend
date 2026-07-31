import enum
import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base_datos.modelos import ModeloBase


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
    fase: Mapped[str] = mapped_column(String(64))  # ej. "Fase II", "Fase III"
    patologia: Mapped[str] = mapped_column(String(120), index=True)
    escenario_clinico: Mapped[str] = mapped_column(String(120))  # ej. "Metastásico", "Adyuvante"
    linea_tratamiento: Mapped[str] = mapped_column(String(64))  # ej. "Primera línea"
    centro_atencion: Mapped[str] = mapped_column(String(120), default="CICUC Principal")
    estado: Mapped[EstadoEstudio] = mapped_column(
        Enum(EstadoEstudio, name="estado_estudio_enum"), default=EstadoEstudio.BORRADOR, index=True
    )
    disponible: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
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


class CohorteEstudio(ModeloBase):
    __tablename__ = "cohortes_estudios"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    estudio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("estudios.id", ondelete="CASCADE"), index=True
    )
    nombre: Mapped[str] = mapped_column(String(120))
    descripcion: Mapped[str | None] = mapped_column(Text)
    biomarcadores_requeridos: Mapped[list[str]] = mapped_column(JSON, default=list)
    meta_reclutamiento: Mapped[int | None] = mapped_column(Integer)

    estudio: Mapped[Estudio] = relationship(back_populates="cohortes")


class VersionProtocolo(ModeloBase):
    __tablename__ = "versiones_protocolo"
    __table_args__ = (
        UniqueConstraint("estudio_id", "numero_version", name="uq_estudio_version_numero"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    estudio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("estudios.id", ondelete="CASCADE"), index=True
    )
    numero_version: Mapped[str] = mapped_column(String(32))  # ej. "v1.0", "v2.1"
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
    orden: Mapped[int] = mapped_column(Integer, default=1)
    codigo_criterio: Mapped[str] = mapped_column(String(32))  # ej. "INC-01", "EXC-02"
    descripcion: Mapped[str] = mapped_column(Text)
    seccion_fuente: Mapped[str | None] = mapped_column(String(120))  # ej. "Sección 4.2.1"
    observaciones: Mapped[str | None] = mapped_column(Text)

    version: Mapped[VersionProtocolo] = relationship(back_populates="criterios")
