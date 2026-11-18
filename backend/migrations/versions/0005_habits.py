"""Habits and habit entries (Fase 7)

Revision ID: 0005_habits
Revises: 0004_widget_boolean
Create Date: 2026-11-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0005_habits"
down_revision: Union[str, None] = "0004_widget_boolean"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- habits ---------------------------------------------------------
    op.create_table(
        "habits",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category", sa.Text(), nullable=True),
        sa.Column("color", sa.String(length=20), nullable=True),
        sa.Column("frequency_type", sa.String(length=20), nullable=False),
        sa.Column("frequency_days", sa.Text(), nullable=True),
        sa.Column("start_date", sa.String(length=10), nullable=False),
        sa.Column("target_value", sa.Float(), nullable=True),
        sa.Column("target_unit", sa.String(length=30), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_habits_status"), "habits", ["status"], unique=False)
    op.create_index(op.f("ix_habits_start_date"), "habits", ["start_date"], unique=False)
    op.create_index(op.f("ix_habits_position"), "habits", ["position"], unique=False)

    # --- habit_entries --------------------------------------------------
    op.create_table(
        "habit_entries",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("habit_id", sa.String(length=36), nullable=False),
        sa.Column("entry_date", sa.String(length=10), nullable=False),
        sa.Column("value", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["habit_id"], ["habits.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "habit_id", "entry_date", name="uq_habit_entries_habit_id_entry_date"
        ),
    )
    op.create_index(
        "ix_habit_entries_habit_id_entry_date",
        "habit_entries",
        ["habit_id", "entry_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_habit_entries_entry_date"),
        "habit_entries",
        ["entry_date"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_habit_entries_entry_date"), table_name="habit_entries")
    op.drop_index("ix_habit_entries_habit_id_entry_date", table_name="habit_entries")
    op.drop_table("habit_entries")
    op.drop_index(op.f("ix_habits_position"), table_name="habits")
    op.drop_index(op.f("ix_habits_start_date"), table_name="habits")
    op.drop_index(op.f("ix_habits_status"), table_name="habits")
    op.drop_table("habits")
