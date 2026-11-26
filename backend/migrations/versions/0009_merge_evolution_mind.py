"""Merge Evolution Home widget and Mind Canvas migration branches.

Revision ID: 0009_merge_evolution_mind
Revises: 0006_home_widget_grid, 0008_mind_canvas_history
Create Date: 2026-11-25

"""

from collections.abc import Sequence

from alembic import op

revision: str = "0009_merge_evolution_mind"
down_revision: tuple[str, str] = (
    "0006_home_widget_grid",
    "0008_mind_canvas_history",
)
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Join the two independently developed schema branches without data changes."""


def downgrade() -> None:
    """Leave both parent revisions in place; no schema changes are required."""
