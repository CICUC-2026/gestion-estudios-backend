"""Persistencia de tareas y reportes operativos HU-021/HU-025."""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260801_0003"
down_revision: str | None = "7d830a34b7e1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    prioridad = postgresql.ENUM("BAJA", "MEDIA", "ALTA", name="prioridad_tarea_enum", create_type=False)
    estado = postgresql.ENUM("PENDIENTE", "EN_CURSO", "BLOQUEADA", "COMPLETADA", "CANCELADA", name="estado_tarea_enum", create_type=False)
    prioridad.create(op.get_bind(), checkfirst=True)
    estado.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "tareas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("titulo", sa.String(160), nullable=False),
        sa.Column("descripcion", sa.Text()),
        sa.Column("prioridad", prioridad, nullable=False),
        sa.Column("estado", estado, nullable=False),
        sa.Column("vence_en", sa.DateTime(timezone=True)),
        sa.Column("creada_por_id", sa.Uuid()),
        sa.Column("responsable_id", sa.Uuid()),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizada_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["creada_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["responsable_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tareas_estado"), "tareas", ["estado"])
    op.create_index(op.f("ix_tareas_prioridad"), "tareas", ["prioridad"])
    op.create_index(op.f("ix_tareas_vence_en"), "tareas", ["vence_en"])
    op.create_table(
        "reportes_operativos",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(160), nullable=False),
        sa.Column("finalidad", sa.String(240), nullable=False),
        sa.Column("fecha_corte", sa.DateTime(timezone=True), nullable=False),
        sa.Column("contenido", sa.JSON(), nullable=False),
        sa.Column("creado_por_id", sa.Uuid()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["creado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_reportes_operativos_fecha_corte"), "reportes_operativos", ["fecha_corte"])


def downgrade() -> None:
    op.drop_table("reportes_operativos")
    op.drop_table("tareas")
    sa.Enum(name="estado_tarea_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="prioridad_tarea_enum").drop(op.get_bind(), checkfirst=True)
