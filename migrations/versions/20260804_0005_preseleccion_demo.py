"""Preselección manual sintética HU-041."""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260804_0005"
down_revision: str | None = "20260804_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    estado_preseleccion = postgresql.ENUM("PENDIENTE_REVISION", "EN_REVISION", "INFORMACION_INCOMPLETA", "POSIBLE_BARRERA", "POSIBLE_ESTUDIO_REVISAR", "DERIVADO_SCREENING_FORMAL", "CERRADO", name="estado_preseleccion_demo_enum", create_type=False)
    estado_evaluacion = postgresql.ENUM("APARENTEMENTE_CUMPLIDO", "PENDIENTE_VERIFICAR", "DUDOSO", "APARENTEMENTE_NO_CUMPLIDO", "NO_CORRESPONDE", name="estado_evaluacion_demo_enum", create_type=False)
    estado_preseleccion.create(op.get_bind(), checkfirst=True)
    estado_evaluacion.create(op.get_bind(), checkfirst=True)
    op.create_table("preselecciones_demo",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("paciente_id", sa.Uuid(), nullable=False), sa.Column("estudio_id", sa.Uuid(), nullable=False), sa.Column("version_id", sa.Uuid(), nullable=False), sa.Column("estado", estado_preseleccion, nullable=False), sa.Column("resumen", sa.Text()), sa.Column("creada_por_id", sa.Uuid()), sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False), sa.Column("actualizada_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["paciente_id"], ["pacientes_demo.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["estudio_id"], ["estudios.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["version_id"], ["versiones_protocolo.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["creada_por_id"], ["usuarios.id"], ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("paciente_id", "version_id", name="uq_preseleccion_demo_paciente_version"))
    for columna in ("paciente_id", "estudio_id", "version_id", "estado"):
        op.create_index(op.f(f"ix_preselecciones_demo_{columna}"), "preselecciones_demo", [columna])
    op.create_table("evaluaciones_criterios_demo",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("preseleccion_id", sa.Uuid(), nullable=False), sa.Column("criterio_id", sa.Uuid(), nullable=False), sa.Column("estado", estado_evaluacion, nullable=False), sa.Column("comentario", sa.Text(), nullable=False), sa.Column("fuente", sa.String(180), nullable=False), sa.Column("autor_id", sa.Uuid()), sa.Column("actualizada_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["preseleccion_id"], ["preselecciones_demo.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["criterio_id"], ["criterios_manuales.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"], ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"), sa.UniqueConstraint("preseleccion_id", "criterio_id", name="uq_evaluacion_demo_preseleccion_criterio"))
    op.create_index(op.f("ix_evaluaciones_criterios_demo_preseleccion_id"), "evaluaciones_criterios_demo", ["preseleccion_id"])
    op.create_index(op.f("ix_evaluaciones_criterios_demo_criterio_id"), "evaluaciones_criterios_demo", ["criterio_id"])
    op.create_table("historial_preselecciones_demo",
        sa.Column("id", sa.Uuid(), nullable=False), sa.Column("preseleccion_id", sa.Uuid(), nullable=False), sa.Column("estado_anterior", sa.String(80)), sa.Column("estado_nuevo", sa.String(80), nullable=False), sa.Column("motivo", sa.Text(), nullable=False), sa.Column("autor_id", sa.Uuid()), sa.Column("fecha", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["preseleccion_id"], ["preselecciones_demo.id"], ondelete="CASCADE"), sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"], ondelete="SET NULL"), sa.PrimaryKeyConstraint("id"))
    op.create_index(op.f("ix_historial_preselecciones_demo_preseleccion_id"), "historial_preselecciones_demo", ["preseleccion_id"])


def downgrade() -> None:
    op.drop_table("historial_preselecciones_demo")
    op.drop_table("evaluaciones_criterios_demo")
    op.drop_table("preselecciones_demo")
    sa.Enum(name="estado_evaluacion_demo_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="estado_preseleccion_demo_enum").drop(op.get_bind(), checkfirst=True)
