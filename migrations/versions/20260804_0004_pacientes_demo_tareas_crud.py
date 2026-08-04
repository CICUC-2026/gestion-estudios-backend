"""Pacientes sintéticos persistentes y tareas relacionadas HU-038/HU-039."""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260804_0004"
down_revision: str | None = "20260801_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    estado = postgresql.ENUM("ANTECEDENTES_PENDIENTES", "REVISION_ADMINISTRATIVA", "INFORMACION_INCOMPLETA", "SEGUIMIENTO_CERRADO", name="estado_paciente_demo_enum", create_type=False)
    estado.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "pacientes_demo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("codigo", sa.String(40), nullable=False),
        sa.Column("rango_etario", sa.String(40), nullable=False),
        sa.Column("patologia", sa.String(160), nullable=False),
        sa.Column("estado", estado, nullable=False),
        sa.Column("sintetico", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("archivado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("creado_por_id", sa.Uuid()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actualizado_en", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("codigo LIKE 'PX-DEMO-%'", name=op.f("ck_pacientes_demo_codigo_sintetico")),
        sa.ForeignKeyConstraint(["creado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("codigo"),
    )
    op.create_index(op.f("ix_pacientes_demo_codigo"), "pacientes_demo", ["codigo"], unique=True)
    op.create_index(op.f("ix_pacientes_demo_patologia"), "pacientes_demo", ["patologia"])
    op.create_index(op.f("ix_pacientes_demo_estado"), "pacientes_demo", ["estado"])
    op.create_index(op.f("ix_pacientes_demo_archivado"), "pacientes_demo", ["archivado"])
    op.create_table(
        "diagnosticos_demo",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("diagnostico", sa.String(180), nullable=False), sa.Column("biomarcador", sa.String(120)),
        sa.Column("resultado_biomarcador", sa.String(120)), sa.Column("fecha", sa.Date(), nullable=False),
        sa.Column("fuente", sa.String(160), nullable=False), sa.Column("creado_por_id", sa.Uuid()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes_demo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creado_por_id"], ["usuarios.id"], ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_diagnosticos_demo_paciente_id"), "diagnosticos_demo", ["paciente_id"])
    op.create_table(
        "paciente_estudios_demo",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("paciente_id", sa.Uuid(), nullable=False),
        sa.Column("estudio_id", sa.Uuid(), nullable=False), sa.Column("estado", sa.String(80), nullable=False),
        sa.Column("observaciones", sa.Text()), sa.Column("creado_por_id", sa.Uuid()),
        sa.Column("creado_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes_demo.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["estudio_id"], ["estudios.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["creado_por_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("paciente_id", "estudio_id", name="uq_paciente_estudio_demo"),
    )
    op.create_index(op.f("ix_paciente_estudios_demo_paciente_id"), "paciente_estudios_demo", ["paciente_id"])
    op.create_index(op.f("ix_paciente_estudios_demo_estudio_id"), "paciente_estudios_demo", ["estudio_id"])
    op.add_column("tareas", sa.Column("paciente_id", sa.Uuid()))
    op.add_column("tareas", sa.Column("estudio_id", sa.Uuid()))
    op.create_foreign_key(op.f("fk_tareas_paciente_id_pacientes_demo"), "tareas", "pacientes_demo", ["paciente_id"], ["id"], ondelete="SET NULL")
    op.create_foreign_key(op.f("fk_tareas_estudio_id_estudios"), "tareas", "estudios", ["estudio_id"], ["id"], ondelete="SET NULL")
    op.create_index(op.f("ix_tareas_paciente_id"), "tareas", ["paciente_id"])
    op.create_index(op.f("ix_tareas_estudio_id"), "tareas", ["estudio_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_tareas_estudio_id"), table_name="tareas")
    op.drop_index(op.f("ix_tareas_paciente_id"), table_name="tareas")
    op.drop_constraint(op.f("fk_tareas_estudio_id_estudios"), "tareas", type_="foreignkey")
    op.drop_constraint(op.f("fk_tareas_paciente_id_pacientes_demo"), "tareas", type_="foreignkey")
    op.drop_column("tareas", "estudio_id"); op.drop_column("tareas", "paciente_id")
    op.drop_table("paciente_estudios_demo"); op.drop_table("diagnosticos_demo"); op.drop_table("pacientes_demo")
    sa.Enum(name="estado_paciente_demo_enum").drop(op.get_bind(), checkfirst=True)
