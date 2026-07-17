"""Crea la base inicial sin entidades clínicas.

Revision ID: 20260717_0001
Revises:
Create Date: 2026-07-17
"""

revision: str = "20260717_0001"
down_revision: str | None = None
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    """Reserva el punto inicial reproducible para migraciones futuras."""


def downgrade() -> None:
    """Revierte la migración base, que todavía no contiene entidades."""
