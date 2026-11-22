"""Persist responsive Home widget grid spans and global order.

Revision ID: 0006_home_widget_grid
Revises: 0005_habits
Create Date: 2026-11-22 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_home_widget_grid"
down_revision: str | None = "0005_habits"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_CAPTURE_IDS = {"quick_add_task", "quick_add_note"}
_MAIN_IDS = {"upcoming_tasks", "active_projects"}
_FULL_IDS = {"habits_week"}
_DEFAULT_SPANS = {
    "upcoming_tasks": (4, 1),
    "active_projects": (4, 1),
    "quick_add_task": (2, 1),
    "quick_add_note": (2, 1),
    "habits_today": (2, 1),
    "habits_week": (6, 1),
}
_LEGACY_ZONE_ORDER = {
    "quick_add_task": 0,
    "quick_add_note": 1,
    "habits_today": 2,
}


def _interleaved_order(rows):
    main = sorted(
        (row for row in rows if row["widget_id"] in _MAIN_IDS),
        key=lambda row: (row["position"], row["widget_id"]),
    )
    side = sorted(
        (row for row in rows if row["widget_id"] not in _MAIN_IDS | _FULL_IDS),
        key=lambda row: (row["position"], row["widget_id"]),
    )

    side_groups = []
    capture = [row for row in side if row["widget_id"] in _CAPTURE_IDS]
    if capture:
        side_groups.append(capture)
    side_groups.extend(
        [[row] for row in side if row["widget_id"] not in _CAPTURE_IDS]
    )
    side_groups.sort(
        key=lambda group: (
            min(row["position"] for row in group),
            min(row["widget_id"] for row in group),
        )
    )

    ordered_groups = []
    for index in range(max(len(main), len(side_groups))):
        if index < len(main):
            ordered_groups.append([main[index]])
        if index < len(side_groups):
            ordered_groups.append(side_groups[index])
    ordered_groups.extend(
        [
            [row]
            for row in sorted(
                (row for row in rows if row["widget_id"] in _FULL_IDS),
                key=lambda row: (row["position"], row["widget_id"]),
            )
        ]
    )
    return ordered_groups


def upgrade() -> None:
    op.add_column(
        "widget_preferences",
        sa.Column("column_span", sa.Integer(), nullable=False, server_default="2"),
    )
    op.add_column(
        "widget_preferences",
        sa.Column("row_span", sa.Integer(), nullable=False, server_default="1"),
    )

    bind = op.get_bind()
    rows = [
        dict(row)
        for row in bind.execute(
            sa.text("SELECT widget_id, position FROM widget_preferences")
        ).mappings()
    ]
    groups = _interleaved_order(rows)
    position = 0
    for group in groups:
        for row in group:
            column_span, row_span = _DEFAULT_SPANS.get(
                row["widget_id"], (2, 1)
            )
            bind.execute(
                sa.text(
                    "UPDATE widget_preferences "
                    "SET position = :position, column_span = :column_span, "
                    "row_span = :row_span WHERE widget_id = :widget_id"
                ),
                {
                    "position": position,
                    "column_span": column_span,
                    "row_span": row_span,
                    "widget_id": row["widget_id"],
                },
            )
        position += 1


def downgrade() -> None:
    bind = op.get_bind()
    rows = [
        dict(row)
        for row in bind.execute(
            sa.text("SELECT widget_id, position FROM widget_preferences")
        ).mappings()
    ]
    zones = {
        "main": _MAIN_IDS,
        "side": _CAPTURE_IDS | {"habits_today"},
        "full": _FULL_IDS,
    }
    for ids in zones.values():
        ordered = sorted(
            (row for row in rows if row["widget_id"] in ids),
            key=lambda row: (
                row["position"],
                _LEGACY_ZONE_ORDER.get(row["widget_id"], 3),
                row["widget_id"],
            ),
        )
        for position, row in enumerate(ordered):
            bind.execute(
                sa.text(
                    "UPDATE widget_preferences SET position = :position "
                    "WHERE widget_id = :widget_id"
                ),
                {"position": position, "widget_id": row["widget_id"]},
            )
    op.drop_column("widget_preferences", "row_span")
    op.drop_column("widget_preferences", "column_span")
