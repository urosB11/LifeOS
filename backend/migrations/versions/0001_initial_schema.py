"""Initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-11-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- projects -------------------------------------------------------
    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.Column("completed_at", sa.String(length=32), nullable=True),
        sa.Column("archived_at", sa.String(length=32), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_status"), "projects", ["status"], unique=False)

    # --- tasks ----------------------------------------------------------
    op.create_table(
        "tasks",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("project_id", sa.String(length=36), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("priority", sa.String(length=10), nullable=True),
        sa.Column("due_date", sa.String(length=10), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.Column("completed_at", sa.String(length=32), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tasks_status"), "tasks", ["status"], unique=False)
    op.create_index(op.f("ix_tasks_due_date"), "tasks", ["due_date"], unique=False)
    op.create_index(op.f("ix_tasks_project_id"), "tasks", ["project_id"], unique=False)

    # --- activity_events ------------------------------------------------
    op.create_table(
        "activity_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=30), nullable=False),
        sa.Column("entity_id", sa.String(length=36), nullable=False),
        sa.Column("occurred_at", sa.String(length=32), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_activity_events_entity_type_entity_id_occurred_at"),
        "activity_events",
        ["entity_type", "entity_id", "occurred_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_activity_events_event_type_occurred_at"),
        "activity_events",
        ["event_type", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_activity_events_event_type_occurred_at"),
        table_name="activity_events",
    )
    op.drop_index(
        op.f("ix_activity_events_entity_type_entity_id_occurred_at"),
        table_name="activity_events",
    )
    op.drop_table("activity_events")
    op.drop_index(op.f("ix_tasks_project_id"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_due_date"), table_name="tasks")
    op.drop_index(op.f("ix_tasks_status"), table_name="tasks")
    op.drop_table("tasks")
    op.drop_index(op.f("ix_projects_status"), table_name="projects")
    op.drop_table("projects")