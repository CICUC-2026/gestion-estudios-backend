import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base_datos.modelos import ModeloBase


class EstadoPreseleccionDemo(str, enum.Enum):
    PENDIENTE_REVISION = "pendiente_revision"
    EN_REVISION = "en_revision"
    INFORMACION_INCOMPLETA = "informacion_incompleta"
    POSIBLE_BARRERA = "posible_barrera"
    POSIBLE_ESTUDIO_REVISAR = "posible_estudio_revisar"
    DERIVADO_SCREENING_FORMAL = "derivado_screening_formal"
    CERRADO = "cerrado"


class EstadoEvaluacionDemo(str, enum.Enum):
    APARENTEMENTE_CUMPLIDO = "aparentemente_cumplido"
    PENDIENTE_VERIFICAR = "pendiente_verificar"
    DUDOSO = "dudoso"
    APARENTEMENTE_NO_CUMPLIDO = "aparentemente_no_cumplido"
    NO_CORRESPONDE = "no_corresponde"


class PreseleccionDemo(ModeloBase):
    __tablename__ = "preselecciones_demo"
    __table_args__ = (
        UniqueConstraint("paciente_id", "version_id", name="uq_preseleccion_demo_paciente_version"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    paciente_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pacientes_demo.id", ondelete="CASCADE"), index=True
    )
    estudio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("estudios.id", ondelete="CASCADE"), index=True
    )
    version_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("versiones_protocolo.id", ondelete="CASCADE"), index=True
    )
    estado: Mapped[EstadoPreseleccionDemo] = mapped_column(
        Enum(EstadoPreseleccionDemo, name="estado_preseleccion_demo_enum"),
        default=EstadoPreseleccionDemo.PENDIENTE_REVISION,
        index=True,
    )
    resumen: Mapped[str | None] = mapped_column(Text)
    creada_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actualizada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    evaluaciones: Mapped[list["EvaluacionCriterioDemo"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )
    historial: Mapped[list["HistorialPreseleccionDemo"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin"
    )


class EvaluacionCriterioDemo(ModeloBase):
    __tablename__ = "evaluaciones_criterios_demo"
    __table_args__ = (
        UniqueConstraint(
            "preseleccion_id", "criterio_id", name="uq_evaluacion_demo_preseleccion_criterio"
        ),
    )
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    preseleccion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("preselecciones_demo.id", ondelete="CASCADE"), index=True
    )
    criterio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("criterios_manuales.id", ondelete="CASCADE"), index=True
    )
    estado: Mapped[EstadoEvaluacionDemo] = mapped_column(
        Enum(EstadoEvaluacionDemo, name="estado_evaluacion_demo_enum")
    )
    comentario: Mapped[str] = mapped_column(Text)
    fuente: Mapped[str] = mapped_column(String(180))
    autor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    actualizada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class HistorialPreseleccionDemo(ModeloBase):
    __tablename__ = "historial_preselecciones_demo"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    preseleccion_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("preselecciones_demo.id", ondelete="CASCADE"), index=True
    )
    estado_anterior: Mapped[str | None] = mapped_column(String(80))
    estado_nuevo: Mapped[str] = mapped_column(String(80))
    motivo: Mapped[str] = mapped_column(Text)
    autor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
