import enum
import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.base_datos.modelos import ModeloBase


class RolUsuario(str, enum.Enum):
    ADMINISTRADOR = "administrador"
    INVESTIGADOR_PRINCIPAL = "investigador_principal"
    MEDICO_INVESTIGADOR = "medico_investigador"
    ENFERMERIA = "enfermeria"
    COORDINADOR = "coordinador"
    AUDITOR = "auditor"


class UsuarioRol(ModeloBase):
    __tablename__ = "usuario_roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    rol: Mapped[RolUsuario] = mapped_column(Enum(RolUsuario, name="rol_usuario_enum"), index=True)
    asignado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    asignado_por_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    usuario: Mapped["Usuario"] = relationship(back_populates="roles", foreign_keys=[usuario_id])


class Usuario(ModeloBase):
    __tablename__ = "usuarios"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    nombres: Mapped[str] = mapped_column(String(120))
    apellidos: Mapped[str] = mapped_column(String(120))
    correo: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    contrasena_hash: Mapped[str] = mapped_column(String(512))
    es_administrador_sistema: Mapped[bool] = mapped_column(Boolean, default=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, default=0)
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ultimo_acceso: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    creado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    actualizado_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    sesiones: Mapped[list["Sesion"]] = relationship(back_populates="usuario")
    roles: Mapped[list["UsuarioRol"]] = relationship(
        back_populates="usuario", foreign_keys=[UsuarioRol.usuario_id], cascade="all, delete-orphan"
    )


class Sesion(ModeloBase):
    __tablename__ = "sesiones"
    __table_args__ = (Index("ix_sesiones_usuario_revocada", "usuario_id", "revocada_en"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    creada_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    ultimo_uso_en: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revocada_en: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    direccion_ip: Mapped[str | None] = mapped_column(String(64))
    agente_usuario: Mapped[str | None] = mapped_column(String(512))

    usuario: Mapped[Usuario] = relationship(back_populates="sesiones")


class RegistroAuditoria(ModeloBase):
    __tablename__ = "registros_auditoria"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    usuario_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL"), index=True
    )
    accion: Mapped[str] = mapped_column(String(120), index=True)
    entidad: Mapped[str] = mapped_column(String(120))
    entidad_id: Mapped[str | None] = mapped_column(String(64))
    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    direccion_ip: Mapped[str | None] = mapped_column(String(64))
    resultado: Mapped[str] = mapped_column(String(40))
    contexto: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    detalle: Mapped[str | None] = mapped_column(Text)
