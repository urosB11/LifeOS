"""Finalize Mind Canvas edges and add the reversible Canvas history.

Revision ID: 0008_mind_canvas_history
Revises: 0007_mind_canvas_edges
Create Date: 2026-11-25

"""

from collections import defaultdict
from collections.abc import Sequence
import json

import sqlalchemy as sa
from alembic import op

revision: str = "0008_mind_canvas_history"
down_revision: str | None = "0007_mind_canvas_edges"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_NODE_PAIR_INDEX = "uq_mind_canvas_nodes_canvas_id_id"
_EDGE_TABLE = "mind_canvas_edges"
_EDGE_REBUILD_TABLE = "mind_canvas_edges_rebuild"
_HISTORY_TABLE = "mind_canvas_history"
_HISTORY_REBUILD_TABLE = "mind_canvas_history_rebuild"


def _column_names(table_name: str) -> set[str]:
    inspector = sa.inspect(op.get_bind())
    if table_name not in inspector.get_table_names():
        return set()
    return {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def _anchor(value: object) -> int:
    try:
        anchor = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
    return anchor if 0 <= anchor <= 7 else 0


def _read_edges() -> list[dict]:
    bind = op.get_bind()
    columns = _column_names(_EDGE_TABLE)
    if not columns:
        return []

    source_anchor = (
        "source_anchor"
        if "source_anchor" in columns
        else "0 AS source_anchor"
    )
    target_anchor = (
        "target_anchor"
        if "target_anchor" in columns
        else "0 AS target_anchor"
    )
    rows = bind.execute(
        sa.text(
            "SELECT id, canvas_id, source_node_id, target_node_id, "
            f"{source_anchor}, {target_anchor}, created_at, updated_at "
            f"FROM {_EDGE_TABLE} ORDER BY created_at, id"
        )
    ).mappings()

    valid_memberships = {
        (row["id"], row["canvas_id"])
        for row in bind.execute(
            sa.text("SELECT id, canvas_id FROM mind_canvas_nodes")
        ).mappings()
    }
    result: list[dict] = []
    pairs: set[tuple[str, str, str]] = set()
    for raw in rows:
        source = raw["source_node_id"]
        target = raw["target_node_id"]
        source_value = _anchor(raw["source_anchor"])
        target_value = _anchor(raw["target_anchor"])
        if source == target:
            raise RuntimeError(
                f"Canvas edge {raw['id']} conecta una Card consigo misma"
            )
        if source > target:
            source, target = target, source
            source_value, target_value = target_value, source_value

        canvas_id = raw["canvas_id"]
        if (source, canvas_id) not in valid_memberships or (
            target,
            canvas_id,
        ) not in valid_memberships:
            raise RuntimeError(
                f"Canvas edge {raw['id']} referencia Cards de otro Canvas"
            )
        pair = (canvas_id, source, target)
        if pair in pairs:
            raise RuntimeError(
                f"Canvas edge {raw['id']} duplica una conexión no dirigida"
            )
        pairs.add(pair)
        result.append(
            {
                "id": raw["id"],
                "canvas_id": canvas_id,
                "source_node_id": source,
                "target_node_id": target,
                "source_anchor": source_value,
                "target_anchor": target_value,
                "created_at": raw["created_at"],
                "updated_at": raw["updated_at"],
            }
        )
    return result


def _create_edges_table(table_name: str, *, final: bool) -> None:
    columns = [
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("canvas_id", sa.String(length=36), nullable=False),
        sa.Column("source_node_id", sa.String(length=36), nullable=False),
        sa.Column("target_node_id", sa.String(length=36), nullable=False),
    ]
    if final:
        columns.extend(
            [
                sa.Column(
                    "source_anchor",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                ),
                sa.Column(
                    "target_anchor",
                    sa.Integer(),
                    nullable=False,
                    server_default="0",
                ),
            ]
        )
    columns.extend(
        [
            sa.Column("created_at", sa.String(length=32), nullable=False),
            sa.Column("updated_at", sa.String(length=32), nullable=False),
        ]
    )

    if final:
        constraints = [
            sa.ForeignKeyConstraint(
                ["canvas_id", "source_node_id"],
                ["mind_canvas_nodes.canvas_id", "mind_canvas_nodes.id"],
                ondelete="CASCADE",
            ),
            sa.ForeignKeyConstraint(
                ["canvas_id", "target_node_id"],
                ["mind_canvas_nodes.canvas_id", "mind_canvas_nodes.id"],
                ondelete="CASCADE",
            ),
        ]
    else:
        constraints = [
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
        ]

    checks = [
        sa.CheckConstraint(
            "source_node_id < target_node_id",
            name="ck_mind_canvas_edges_source_lt_target",
        )
    ]
    if final:
        checks.extend(
            [
                sa.CheckConstraint(
                    "source_anchor BETWEEN 0 AND 7",
                    name="ck_mind_canvas_edges_source_anchor",
                ),
                sa.CheckConstraint(
                    "target_anchor BETWEEN 0 AND 7",
                    name="ck_mind_canvas_edges_target_anchor",
                ),
            ]
        )

    op.create_table(
        table_name,
        *columns,
        *constraints,
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canvas_id",
            "source_node_id",
            "target_node_id",
            name="uq_mind_canvas_edges_canvas_source_target",
        ),
        *checks,
    )


def _rebuild_edges(*, final: bool) -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = _EDGE_TABLE in inspector.get_table_names()
    rows = _read_edges() if existing else []

    if _EDGE_REBUILD_TABLE in inspector.get_table_names():
        op.drop_table(_EDGE_REBUILD_TABLE)

    _create_edges_table(_EDGE_REBUILD_TABLE, final=final)

    insert_columns = [
        "id",
        "canvas_id",
        "source_node_id",
        "target_node_id",
    ]
    if final:
        insert_columns.extend(["source_anchor", "target_anchor"])
    insert_columns.extend(["created_at", "updated_at"])
    statement = sa.text(
        f"INSERT INTO {_EDGE_REBUILD_TABLE} "
        f"({', '.join(insert_columns)}) VALUES "
        f"({', '.join(':' + column for column in insert_columns)})"
    )
    for row in rows:
        bind.execute(statement, row)

    if existing:
        op.drop_table(_EDGE_TABLE)
    op.rename_table(_EDGE_REBUILD_TABLE, _EDGE_TABLE)
    op.create_index(
        "ix_mind_canvas_edges_canvas_source",
        _EDGE_TABLE,
        ["canvas_id", "source_node_id"],
    )
    op.create_index(
        "ix_mind_canvas_edges_canvas_target",
        _EDGE_TABLE,
        ["canvas_id", "target_node_id"],
    )


def _history_state(snapshot: str, stored: object) -> str:
    try:
        envelope = json.loads(snapshot)
    except (TypeError, json.JSONDecodeError):
        envelope = {}
    if isinstance(envelope, dict):
        if envelope.get("discarded"):
            return "discarded"
        if envelope.get("undone"):
            return "undone"
    return stored if stored in {"applied", "undone", "discarded"} else "applied"


def _read_history() -> list[dict]:
    bind = op.get_bind()
    columns = _column_names(_HISTORY_TABLE)
    if not columns:
        return []

    required = {
        "id",
        "canvas_id",
        "action_type",
        "snapshot_json",
        "created_at",
    }
    missing = required - columns
    if missing:
        raise RuntimeError(
            "mind_canvas_history no contiene las columnas requeridas: "
            + ", ".join(sorted(missing))
        )

    selected = [
        "id",
        "canvas_id",
        "action_type",
        "snapshot_json",
        "created_at",
    ]
    optional = {
        "inverse_json": "NULL AS inverse_json",
        "request_key": "NULL AS request_key",
        "state": "'applied' AS state",
        "undone_at": "NULL AS undone_at",
    }
    for column, expression in optional.items():
        if column in columns:
            selected.append(column)
        else:
            selected.append(expression)

    raw_rows = list(
        bind.execute(
            sa.text(
                f"SELECT {', '.join(selected)} FROM mind_canvas_history "
                "ORDER BY canvas_id, created_at, id"
            )
        ).mappings()
    )
    sequences: defaultdict[str, int] = defaultdict(int)
    requests: set[tuple[str, str]] = set()
    result: list[dict] = []
    for raw in raw_rows:
        canvas_id = raw["canvas_id"]
        sequences[canvas_id] += 1
        request_key = raw["request_key"]
        if request_key:
            request_pair = (canvas_id, request_key)
            if request_pair in requests:
                request_key = None
            else:
                requests.add(request_pair)
        result.append(
            {
                "id": raw["id"],
                "canvas_id": canvas_id,
                "sequence": sequences[canvas_id],
                "action_type": raw["action_type"],
                "snapshot_json": raw["snapshot_json"],
                "inverse_json": raw["inverse_json"],
                "request_key": request_key,
                "state": _history_state(raw["snapshot_json"], raw["state"]),
                "undone_at": raw["undone_at"],
                "created_at": raw["created_at"],
            }
        )
    return result


def _create_history_table(table_name: str) -> None:
    op.create_table(
        table_name,
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("canvas_id", sa.String(length=36), nullable=False),
        sa.Column("sequence", sa.Integer(), nullable=False),
        sa.Column("action_type", sa.String(length=30), nullable=False),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("inverse_json", sa.Text(), nullable=True),
        sa.Column("request_key", sa.String(length=64), nullable=True),
        sa.Column(
            "state",
            sa.String(length=12),
            nullable=False,
            server_default="applied",
        ),
        sa.Column("undone_at", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(
            ["canvas_id"],
            ["mind_canvases.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "canvas_id",
            "sequence",
            name="uq_mind_canvas_history_canvas_sequence",
        ),
        sa.UniqueConstraint(
            "canvas_id",
            "request_key",
            name="uq_mind_canvas_history_canvas_request_key",
        ),
        sa.CheckConstraint(
            "state IN ('applied', 'undone', 'discarded')",
            name="ck_mind_canvas_history_state",
        ),
    )


def _rebuild_history() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = _HISTORY_TABLE in inspector.get_table_names()
    rows = _read_history() if existing else []

    if _HISTORY_REBUILD_TABLE in inspector.get_table_names():
        op.drop_table(_HISTORY_REBUILD_TABLE)
    _create_history_table(_HISTORY_REBUILD_TABLE)
    statement = sa.text(
        "INSERT INTO mind_canvas_history_rebuild "
        "(id, canvas_id, sequence, action_type, snapshot_json, inverse_json, "
        "request_key, state, undone_at, created_at) VALUES "
        "(:id, :canvas_id, :sequence, :action_type, :snapshot_json, "
        ":inverse_json, :request_key, :state, :undone_at, :created_at)"
    )
    for row in rows:
        bind.execute(statement, row)
    if existing:
        op.drop_table(_HISTORY_TABLE)
    op.rename_table(_HISTORY_REBUILD_TABLE, _HISTORY_TABLE)
    op.create_index(
        "ix_mind_canvas_history_canvas_created",
        _HISTORY_TABLE,
        ["canvas_id", "created_at"],
    )


def upgrade() -> None:
    """Reconcile legacy tables and create the final Canvas schema."""
    inspector = sa.inspect(op.get_bind())
    node_indexes = {
        index["name"]
        for index in inspector.get_indexes("mind_canvas_nodes")
    }
    if _NODE_PAIR_INDEX not in node_indexes:
        op.create_index(
            _NODE_PAIR_INDEX,
            "mind_canvas_nodes",
            ["canvas_id", "id"],
            unique=True,
        )

    _rebuild_edges(final=True)
    _rebuild_history()


def downgrade() -> None:
    """Restore the edge shape owned by revision 0007 and remove history."""
    inspector = sa.inspect(op.get_bind())
    if _HISTORY_TABLE in inspector.get_table_names():
        op.drop_table(_HISTORY_TABLE)

    _rebuild_edges(final=False)

    node_indexes = {
        index["name"]
        for index in sa.inspect(op.get_bind()).get_indexes("mind_canvas_nodes")
    }
    if _NODE_PAIR_INDEX in node_indexes:
        op.drop_index(
            _NODE_PAIR_INDEX,
            table_name="mind_canvas_nodes",
        )
