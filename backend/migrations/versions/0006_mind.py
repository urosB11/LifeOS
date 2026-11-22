"""Mind: spaces, canvases, memberships and canvas nodes (MIND-002)

Revision ID: 0006_mind
Revises: 0005_habits
Create Date: 2026-11-22 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006_mind"
down_revision: Union[str, None] = "0005_habits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- mind_spaces ------------------------------------------------------
    # `is_inbox` con índice único parcial: a lo sumo un Inbox por instalación.
    op.create_table(
        "mind_spaces",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_inbox", sa.Boolean(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("archived_at", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mind_spaces_status", "mind_spaces", ["status"])
    op.create_index(
        "uq_mind_spaces_is_inbox",
        "mind_spaces",
        ["is_inbox"],
        unique=True,
        sqlite_where=sa.text("is_inbox = 1"),
    )

    # --- mind_canvases ----------------------------------------------------
    op.create_table(
        "mind_canvases",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("space_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("archived_at", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["space_id"], ["mind_spaces.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_mind_canvases_space_id", "mind_canvases", ["space_id"])
    op.create_index("ix_mind_canvases_status", "mind_canvases", ["status"])

    # --- mind_space_notes -------------------------------------------------
    # Membresía Note↔Space (Inbox incluido). PK compuesta.
    op.create_table(
        "mind_space_notes",
        sa.Column("space_id", sa.String(length=36), nullable=False),
        sa.Column("note_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["space_id"], ["mind_spaces.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["note_id"], ["notes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("space_id", "note_id"),
    )
    op.create_index("ix_mind_space_notes_note_id", "mind_space_notes", ["note_id"])

    # --- mind_canvas_nodes ------------------------------------------------
    # Instancia visual de una Note: posición en coordenadas del mundo.
    op.create_table(
        "mind_canvas_nodes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("canvas_id", sa.String(length=36), nullable=False),
        sa.Column("note_id", sa.String(length=36), nullable=False),
        sa.Column("x", sa.Float(), nullable=False),
        sa.Column("y", sa.Float(), nullable=False),
        sa.Column("width", sa.Float(), nullable=True),
        sa.Column("height", sa.Float(), nullable=True),
        sa.Column("z_index", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["canvas_id"], ["mind_canvases.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["note_id"], ["notes.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canvas_id", "note_id", name="uq_mind_canvas_nodes_canvas_id_note_id"
        ),
    )
    op.create_index("ix_mind_canvas_nodes_canvas_id", "mind_canvas_nodes", ["canvas_id"])
    op.create_index("ix_mind_canvas_nodes_note_id", "mind_canvas_nodes", ["note_id"])


def downgrade() -> None:
    op.drop_index("ix_mind_canvas_nodes_note_id", table_name="mind_canvas_nodes")
    op.drop_index("ix_mind_canvas_nodes_canvas_id", table_name="mind_canvas_nodes")
    op.drop_table("mind_canvas_nodes")

    op.drop_index("ix_mind_space_notes_note_id", table_name="mind_space_notes")
    op.drop_table("mind_space_notes")

    op.drop_index("ix_mind_canvases_status", table_name="mind_canvases")
    op.drop_index("ix_mind_canvases_space_id", table_name="mind_canvases")
    op.drop_table("mind_canvases")

    op.drop_index("uq_mind_spaces_is_inbox", table_name="mind_spaces")
    op.drop_index("ix_mind_spaces_status", table_name="mind_spaces")
    op.drop_table("mind_spaces")
