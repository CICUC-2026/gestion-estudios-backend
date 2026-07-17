"""Crea usuarios, sesiones y auditoría inicial.

Revision ID: 20260717_0002
Revises: 20260717_0001
Create Date: 2026-07-17
"""

import sqlalchemy as sa
from alembic import op

revision: str = "20260717_0002"
down_revision: str | None = "20260717_0001"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombres", sa.String(length=120), nullable=False),
        sa.Column("apellidos", sa.String(length=120), nullable=False),
        sa.Column("correo", sa.String(length=320), nullable=False),
        sa.Column("contrasena_hash", sa.String(length=512), nullable=False),
        sa.Column("es_administrador_sistema", sa.Boolean(), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column("intentos_fallidos", sa.Integer(), nullable=False),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ultimo_acceso", sa.DateTime(timezone=True), nullable=True),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuarios")),
    )
    op.create_index(op.f("ix_usuarios_activo"), "usuarios", ["activo"])
    op.create_index(op.f("ix_usuarios_correo"), "usuarios", ["correo"], unique=True)

    op.create_table(
        "sesiones",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ultimo_uso_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revocada_en", sa.DateTime(timezone=True), nullable=True),
        sa.Column("direccion_ip", sa.String(length=64), nullable=True),
        sa.Column("agente_usuario", sa.String(length=512), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("fk_sesiones_usuario_id_usuarios"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sesiones")),
    )
    op.create_index(op.f("ix_sesiones_expira_en"), "sesiones", ["expira_en"])
    op.create_index(op.f("ix_sesiones_token_hash"), "sesiones", ["token_hash"], unique=True)
    op.create_index(op.f("ix_sesiones_usuario_id"), "sesiones", ["usuario_id"])
    op.create_index("ix_sesiones_usuario_revocada", "sesiones", ["usuario_id", "revocada_en"])

    op.create_table(
        "registros_auditoria",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("usuario_id", sa.Uuid(), nullable=True),
        sa.Column("accion", sa.String(length=120), nullable=False),
        sa.Column("entidad", sa.String(length=120), nullable=False),
        sa.Column("entidad_id", sa.String(length=64), nullable=True),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.Column("direccion_ip", sa.String(length=64), nullable=True),
        sa.Column("resultado", sa.String(length=40), nullable=False),
        sa.Column("contexto", sa.JSON(), nullable=False),
        sa.Column("detalle", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("fk_registros_auditoria_usuario_id_usuarios"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_registros_auditoria")),
    )
    op.create_index(op.f("ix_registros_auditoria_accion"), "registros_auditoria", ["accion"])
    op.create_index(op.f("ix_registros_auditoria_fecha"), "registros_auditoria", ["fecha"])
    op.create_index(
        op.f("ix_registros_auditoria_usuario_id"), "registros_auditoria", ["usuario_id"]
    )


def downgrade() -> None:
    op.drop_table("registros_auditoria")
    op.drop_table("sesiones")
    op.drop_table("usuarios")
