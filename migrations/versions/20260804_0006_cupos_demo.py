"""Cupos y reservas sintéticas HU-042."""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260804_0006"
down_revision: str | None = "20260804_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    estado = postgresql.ENUM(
        "CONFIRMADO", "RESERVADO", "OCUPADO", "PENDIENTE_RECONFIRMACION", "CANCELADO",
        name="estado_cupo_demo_enum", create_type=False,
    )
    estado.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "cupos_demo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("estudio_id", sa.Uuid(), nullable=False),
        sa.Column("paciente_id", sa.Uuid()),
        sa.Column("estado", estado, nullable=False),
        sa.Column("fuente", sa.String(180), nullable=False),
        sa.Column("responsable_id", sa.Uuid()),
        sa.Column("dias_validez", sa.Integer(), nullable=False),
        sa.Column("confirmado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("vence_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["estudio_id"], ["estudios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes_demo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for columna in ("estudio_id", "paciente_id", "estado", "vence_en"):
        op.create_index(op.f(f"ix_cupos_demo_{columna}"), "cupos_demo", [columna])
    op.create_table(
        "historial_cupos_demo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cupo_id", sa.Uuid(), nullable=False),
        sa.Column("estado_anterior", sa.String(80)),
        sa.Column("estado_nuevo", sa.String(80), nullable=False),
        sa.Column("paciente_id", sa.Uuid()),
        sa.Column("motivo", sa.Text(), nullable=False),
        sa.Column("autor_id", sa.Uuid()),
        sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["cupo_id"], ["cupos_demo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes_demo.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_historial_cupos_demo_cupo_id"), "historial_cupos_demo", ["cupo_id"])


def downgrade() -> None:
    op.drop_table("historial_cupos_demo")
    op.drop_table("cupos_demo")
    sa.Enum(name="estado_cupo_demo_enum").drop(op.get_bind(), checkfirst=True)
