import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.base_datos.modelos import ModeloBase


class EstadoPacienteDemo(str, enum.Enum):
    ANTECEDENTES_PENDIENTES = "antecedentes_pendientes"
    REVISION_ADMINISTRATIVA = "revision_administrativa"
    INFORMACION_INCOMPLETA = "informacion_incompleta"
    SEGUIMIENTO_CERRADO = "seguimiento_cerrado"


class PacienteDemo(ModeloBase):
    __tablename__ = "pacientes_demo"
    __table_args__ = (CheckConstraint("codigo LIKE 'PX-DEMO-%'", name="codigo_sintetico"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    codigo: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    rango_etario: Mapped[str] = mapped_column(String(40))
    patologia: Mapped[str] = mapped_column(String(160), index=True)
    estado: Mapped[EstadoPacienteDemo] = mapped_column(
        Enum(EstadoPacienteDemo, name="estado_paciente_demo_enum"), index=True
    )
    sintetico: Mapped[bool] = mapped_column(Boolean, default=True)
    archivado: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class DiagnosticoDemo(ModeloBase):
    __tablename__ = "diagnosticos_demo"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pacientes_demo.id", ondelete="CASCADE"), index=True
    )
    diagnostico: Mapped[str] = mapped_column(String(180))
    biomarcador: Mapped[str | None] = mapped_column(String(120))
    resultado_biomarcador: Mapped[str | None] = mapped_column(String(120))
    fecha: Mapped[date] = mapped_column(Date)
    fuente: Mapped[str] = mapped_column(String(160))
    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class PacienteEstudioDemo(ModeloBase):
    __tablename__ = "paciente_estudios_demo"
    __table_args__ = (
        UniqueConstraint("paciente_id", "estudio_id", name="uq_paciente_estudio_demo"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pacientes_demo.id", ondelete="CASCADE"), index=True
    )
    estudio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("estudios.id", ondelete="CASCADE"), index=True
    )
    estado: Mapped[str] = mapped_column(String(80), default="pendiente_revision")
    observaciones: Mapped[str | None] = mapped_column(Text)
    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
