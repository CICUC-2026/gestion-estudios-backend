import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.base_datos.modelos import ModeloBase


class FormatoExportacion(str, enum.Enum):
    XLSX = "xlsx"
    CSV = "csv"
    JSON = "json"
    TXT = "txt"


class ExportacionDemo(ModeloBase):
    __tablename__ = "exportaciones_demo"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    finalidad: Mapped[str] = mapped_column(String(240))
    formato: Mapped[FormatoExportacion] = mapped_column(
        Enum(FormatoExportacion, name="formato_exportacion_demo_enum"), index=True
    )
    filtros: Mapped[dict[str, Any]] = mapped_column(JSON)
    campos: Mapped[list[str]] = mapped_column(JSON)
    cantidad: Mapped[int] = mapped_column(Integer)
    hash_sha256: Mapped[str] = mapped_column(String(64), index=True)
    autor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
