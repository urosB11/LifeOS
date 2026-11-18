"""Dashboard widgets and user preferences

Revision ID: 0003_dashboard_settings
Revises: 0002_notes_tags
Create Date: 2026-11-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_dashboard_settings"
down_revision: Union[str, None] = "0002_notes_tags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- widget_preferences ---------------------------------------------
    op.create_table(
        "widget_preferences",
        sa.Column("widget_id", sa.String(length=50), nullable=False),
        sa.Column("is_visible", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("widget_id"),
    )

    # --- user_preferences -----------------------------------------------
    op.create_table(
        "user_preferences",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )


def downgrade() -> None:
    op.drop_table("user_preferences")
    op.drop_table("widget_preferences")