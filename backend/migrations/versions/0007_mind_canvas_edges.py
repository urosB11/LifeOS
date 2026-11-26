"""Create the Mind Canvas edge table.

Revision ID: 0007_mind_canvas_edges
Revises: 0006_mind
Create Date: 2026-11-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_mind_canvas_edges"
down_revision: str | None = "0006_mind"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create Canvas edges without assuming an unversioned table exists.

    Revision 0008 reconciles legacy tables to the final composite-FK schema.
    """
    inspector = sa.inspect(op.get_bind())
    if "mind_canvas_edges" in inspector.get_table_names():
        return

    op.create_table(
        "mind_canvas_edges",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("canvas_id", sa.String(length=36), nullable=False),
        sa.Column("source_node_id", sa.String(length=36), nullable=False),
        sa.Column("target_node_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["canvas_id"],
            ["mind_canvases.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_node_id"],
            ["mind_canvas_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["target_node_id"],
            ["mind_canvas_nodes.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canvas_id",
            "source_node_id",
            "target_node_id",
            name="uq_mind_canvas_edges_canvas_source_target",
        ),
        sa.CheckConstraint(
            "source_node_id < target_node_id",
            name="ck_mind_canvas_edges_source_lt_target",
        ),
    )
    op.create_index(
        "ix_mind_canvas_edges_canvas_source",
        "mind_canvas_edges",
        ["canvas_id", "source_node_id"],
    )
    op.create_index(
        "ix_mind_canvas_edges_canvas_target",
        "mind_canvas_edges",
        ["canvas_id", "target_node_id"],
    )


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "mind_canvas_edges" not in inspector.get_table_names():
        return
    op.drop_index(
        "ix_mind_canvas_edges_canvas_target",
        table_name="mind_canvas_edges",
    )
    op.drop_index(
        "ix_mind_canvas_edges_canvas_source",
        table_name="mind_canvas_edges",
    )
    op.drop_table("mind_canvas_edges")
