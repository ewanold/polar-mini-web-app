"""Initialize the application schema.

Revision ID: 0001
Revises:
Create Date: 2026-09-02
"""

from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Initialize an empty schema reserved for later domain models."""


def downgrade() -> None:
    """Remove the empty initial schema."""
