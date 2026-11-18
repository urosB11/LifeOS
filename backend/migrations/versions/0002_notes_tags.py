"""Notes, tags and links

Revision ID: 0002_notes_tags
Revises: 0001_initial_schema
Create Date: 2026-11-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002_notes_tags"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- notes ----------------------------------------------------------
    op.create_table(
        "notes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_notes_updated_at"), "notes", ["updated_at"], unique=False)

    # --- note_project_links ---------------------------------------------
    op.create_table(
        "note_project_links",
        sa.Column("note_id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["note_id"], ["notes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["project_id"], ["projects.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("note_id", "project_id"),
    )
    op.create_index(
        op.f("ix_note_project_links_project_id"),
        "note_project_links",
        ["project_id"],
        unique=False,
    )

    # --- note_task_links ------------------------------------------------
    op.create_table(
        "note_task_links",
        sa.Column("note_id", sa.String(length=36), nullable=False),
        sa.Column("task_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["note_id"], ["notes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["task_id"], ["tasks.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("note_id", "task_id"),
    )
    op.create_index(
        op.f("ix_note_task_links_task_id"),
        "note_task_links",
        ["task_id"],
        unique=False,
    )

    # --- tags -----------------------------------------------------------
    op.create_table(
        "tags",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("normalized_name", sa.String(length=200), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name", name="uq_tags_normalized_name"),
    )
    op.create_index(op.f("ix_tags_normalized_name"), "tags", ["normalized_name"], unique=True)

    # --- note_tags ------------------------------------------------------
    op.create_table(
        "note_tags",
        sa.Column("note_id", sa.String(length=36), nullable=False),
        sa.Column("tag_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["note_id"], ["notes.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"], ["tags.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("note_id", "tag_id"),
    )
    op.create_index(
        op.f("ix_note_tags_tag_id"),
        "note_tags",
        ["tag_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_note_tags_tag_id"), table_name="note_tags")
    op.drop_table("note_tags")
    op.drop_index(op.f("ix_tags_normalized_name"), table_name="tags")
    op.drop_table("tags")
    op.drop_index(op.f("ix_note_task_links_task_id"), table_name="note_task_links")
    op.drop_table("note_task_links")
    op.drop_index(op.f("ix_note_project_links_project_id"), table_name="note_project_links")
    op.drop_table("note_project_links")
    op.drop_index(op.f("ix_notes_updated_at"), table_name="notes")
    op.drop_table("notes")