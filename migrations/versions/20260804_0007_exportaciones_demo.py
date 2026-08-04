"""Exportaciones sintéticas autorizadas HU-043."""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260804_0007"
down_revision: str | None = "20260804_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    formato = postgresql.ENUM(
        "XLSX", "CSV", "JSON", "TXT", name="formato_exportacion_demo_enum", create_type=False
    )
    formato.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "exportaciones_demo",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("finalidad", sa.String(240), nullable=False),
        sa.Column("formato", formato, nullable=False),
        sa.Column("filtros", sa.JSON(), nullable=False),
        sa.Column("campos", sa.JSON(), nullable=False),
        sa.Column("cantidad", sa.Integer(), nullable=False),
        sa.Column("hash_sha256", sa.String(64), nullable=False),
        sa.Column("autor_id", sa.Uuid()),
        sa.Column("creada_en", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["autor_id"], ["usuarios.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    for columna in ("formato", "hash_sha256", "autor_id", "creada_en"):
        op.create_index(op.f(f"ix_exportaciones_demo_{columna}"), "exportaciones_demo", [columna])


def downgrade() -> None:
    op.drop_table("exportaciones_demo")
    sa.Enum(name="formato_exportacion_demo_enum").drop(op.get_bind(), checkfirst=True)
