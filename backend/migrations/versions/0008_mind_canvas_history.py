"""add mind_canvas_history table for undo/redo

Revision ID: 0008_mind_canvas_history
Revises: 0007_mind_canvas_edges
Create Date: 2026-11-25 15:38:42.279926

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0008_mind_canvas_history"
down_revision: Union[str, None] = "0007_mind_canvas_edges"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "mind_canvas_history",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("canvas_id", sa.String(length=36), nullable=False),
        sa.Column("action_type", sa.String(length=30), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("inverse_json", sa.Text(), nullable=True),
        sa.Column("request_key", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["canvas_id"],
            ["mind_canvases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_mind_canvas_history_canvas_created",
        "mind_canvas_history",
        ["canvas_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_mind_canvas_history_canvas_created",
        table_name="mind_canvas_history",
    )
    op.drop_table("mind_canvas_history")
