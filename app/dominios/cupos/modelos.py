import enum
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base_datos.modelos import ModeloBase


class EstadoCupoDemo(str, enum.Enum):
    CONFIRMADO = "confirmado"
    RESERVADO = "reservado"
    OCUPADO = "ocupado"
    PENDIENTE_RECONFIRMACION = "pendiente_reconfirmacion"
    CANCELADO = "cancelado"


class CupoDemo(ModeloBase):
    __tablename__ = "cupos_demo"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    estudio_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("estudios.id", ondelete="CASCADE"), index=True
    )
    paciente_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pacientes_demo.id", ondelete="RESTRICT"), index=True
    )
    estado: Mapped[EstadoCupoDemo] = mapped_column(
        Enum(EstadoCupoDemo, name="estado_cupo_demo_enum"), index=True
    )
    fuente: Mapped[str] = mapped_column(String(180))
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    dias_validez: Mapped[int] = mapped_column(Integer)
    confirmado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    vence_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    historial: Mapped[list["HistorialCupoDemo"]] = relationship(
        cascade="all, delete-orphan", lazy="selectin", order_by="HistorialCupoDemo.fecha"
    )

    @property
    def vencido(self) -> bool:
        return self.vence_en <= datetime.now(UTC)

    @property
    def vence_pronto(self) -> bool:
        ahora = datetime.now(UTC)
        return ahora < self.vence_en <= ahora + timedelta(days=7)


class HistorialCupoDemo(ModeloBase):
    __tablename__ = "historial_cupos_demo"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    cupo_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("cupos_demo.id", ondelete="CASCADE"), index=True
    )
    estado_anterior: Mapped[str | None] = mapped_column(String(80))
    estado_nuevo: Mapped[str] = mapped_column(String(80))
    paciente_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("pacientes_demo.id", ondelete="RESTRICT")
    )
    motivo: Mapped[str] = mapped_column(Text)
    autor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True))
