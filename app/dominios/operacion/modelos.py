import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.base_datos.modelos import ModeloBase


class PrioridadTarea(str, enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"


class EstadoTarea(str, enum.Enum):
    PENDIENTE = "pendiente"
    EN_CURSO = "en_curso"
    BLOQUEADA = "bloqueada"
    COMPLETADA = "completada"
    CANCELADA = "cancelada"


class Tarea(ModeloBase):
    __tablename__ = "tareas"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    titulo: Mapped[str] = mapped_column(String(160))
    descripcion: Mapped[str | None] = mapped_column(Text)
    prioridad: Mapped[PrioridadTarea] = mapped_column(
        Enum(PrioridadTarea, name="prioridad_tarea_enum"), index=True
    )
    estado: Mapped[EstadoTarea] = mapped_column(
        Enum(EstadoTarea, name="estado_tarea_enum"), index=True
    )
    vence_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    creada_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    responsable_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actualizada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class ReporteOperativo(ModeloBase):
    __tablename__ = "reportes_operativos"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nombre: Mapped[str] = mapped_column(String(160))
    finalidad: Mapped[str] = mapped_column(String(240))
    fecha_corte: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    contenido: Mapped[dict[str, Any]] = mapped_column(JSON)
    creado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
