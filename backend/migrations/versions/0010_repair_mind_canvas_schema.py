"""Repair the physical Mind Canvas schema without rewriting earlier revisions.

Revision ID: 0010_repair_mind_canvas_schema
Revises: 0009_merge_evolution_mind
Create Date: 2026-11-27

Databases stamped at ``0008_mind_canvas_history`` may still have the physical
schema from the pre-merge lineage: history without ``sequence``/``state``/
``undone_at`` and edges with legacy metadata columns. This revision rebuilds
only the tables whose final shape is not already present. It is a no-op on a
fresh database and refuses to discard legacy edge metadata silently.

``downgrade()`` is intentionally a no-op: revision 0009 already expects the
final schema, and removing history columns would destroy information. A real
rollback is a verified SQLite backup, not ``alembic downgrade``.
"""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_repair_mind_canvas_schema"
down_revision: str | None = "0009_merge_evolution_mind"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_HISTORY = "mind_canvas_history"
_EDGES = "mind_canvas_edges"
_NODES = "mind_canvas_nodes"
_HISTORY_TMP = "mind_canvas_history_0010"
_EDGES_TMP = "mind_canvas_edges_0010"
_NODE_PAIR_INDEX = "uq_mind_canvas_nodes_canvas_id_id"

_HISTORY_COLUMN_SPECS: dict[str, tuple[str, bool, str | None]] = {
    "id": ("VARCHAR(36)", False, None),
    "canvas_id": ("VARCHAR(36)", False, None),
    "sequence": ("INTEGER", False, None),
    "action_type": ("VARCHAR(30)", False, None),
    "snapshot_json": ("TEXT", False, None),
    "inverse_json": ("TEXT", True, None),
    "request_key": ("VARCHAR(64)", True, None),
    "state": ("VARCHAR(12)", False, "applied"),
    "undone_at": ("VARCHAR(32)", True, None),
    "created_at": ("VARCHAR(32)", False, None),
}
_EDGE_COLUMN_SPECS: dict[str, tuple[str, bool, str | None]] = {
    "id": ("VARCHAR(36)", False, None),
    "canvas_id": ("VARCHAR(36)", False, None),
    "source_node_id": ("VARCHAR(36)", False, None),
    "target_node_id": ("VARCHAR(36)", False, None),
    "source_anchor": ("INTEGER", False, "0"),
    "target_anchor": ("INTEGER", False, "0"),
    "created_at": ("VARCHAR(32)", False, None),
    "updated_at": ("VARCHAR(32)", False, None),
}
_HISTORY_UNIQUES = {
    "uq_mind_canvas_history_canvas_sequence": ("canvas_id", "sequence"),
    "uq_mind_canvas_history_canvas_request_key": ("canvas_id", "request_key"),
}
_HISTORY_CHECKS = {
    "ck_mind_canvas_history_state": "state in ('applied', 'undone', 'discarded')",
}
_HISTORY_INDEX = ("ix_mind_canvas_history_canvas_created", ("canvas_id", "created_at"))
_EDGE_UNIQUES = {
    "uq_mind_canvas_edges_canvas_source_target": (
        "canvas_id",
        "source_node_id",
        "target_node_id",
    ),
}
_EDGE_CHECKS = {
    "ck_mind_canvas_edges_source_lt_target": "source_node_id < target_node_id",
    "ck_mind_canvas_edges_source_anchor": "source_anchor between 0 and 7",
    "ck_mind_canvas_edges_target_anchor": "target_anchor between 0 and 7",
}
_EDGE_INDEXES = {
    "ix_mind_canvas_edges_canvas_source": ("canvas_id", "source_node_id"),
    "ix_mind_canvas_edges_canvas_target": ("canvas_id", "target_node_id"),
}
_EDGE_FKS = {
    (
        ("canvas_id", "source_node_id"),
        "mind_canvas_nodes",
        ("canvas_id", "id"),
        "CASCADE",
    ),
    (
        ("canvas_id", "target_node_id"),
        "mind_canvas_nodes",
        ("canvas_id", "id"),
        "CASCADE",
    ),
}
_HISTORY_FKS = {
    (
        ("canvas_id",),
        "mind_canvases",
        ("id",),
        "CASCADE",
    ),
}
_HISTORY_REQUIRED = {
    "id",
    "canvas_id",
    "action_type",
    "snapshot_json",
    "created_at",
}
_EDGE_REQUIRED = {
    "id",
    "canvas_id",
    "source_node_id",
    "target_node_id",
    "created_at",
    "updated_at",
}
_EDGE_LEGACY_COLUMNS = {
    "edge_type",
    "style_json",
    "ai_suggested",
    "ai_confidence",
}


class _Plan:
    def __init__(
        self,
        action: str,
        *,
        rows: list[dict] | None = None,
        reason: str = "",
    ) -> None:
        self.action = action
        self.rows = rows or []
        self.reason = reason


def _inspector() -> sa.Inspector:
    return sa.inspect(op.get_bind())


def _table_exists(inspector: sa.Inspector, table: str) -> bool:
    return table in inspector.get_table_names()


def _table_sql(table: str) -> str:
    value = op.get_bind().execute(
        sa.text(
            "SELECT sql FROM sqlite_master "
            "WHERE type = 'table' AND name = :name"
        ),
        {"name": table},
    ).scalar()
    return value or ""


def _norm_sql(value: object) -> str:
    text = str(value or "").lower()
    for token in ('"', "`", " ", "\n", "\r", "\t"):
        text = text.replace(token, "")
    return text


def _norm_default(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in {"'", '"'}:
        text = text[1:-1]
    return text.lower()


def _column_mismatches(
    inspector: sa.Inspector,
    table: str,
    specs: dict[str, tuple[str, bool, str | None]],
) -> list[str]:
    actual = {column["name"]: column for column in inspector.get_columns(table)}
    problems: list[str] = []
    for name, (type_name, nullable, default) in specs.items():
        column = actual.get(name)
        if column is None:
            problems.append(f"falta la columna {name}")
            continue
        actual_type = str(column["type"]).upper()
        if actual_type != type_name:
            problems.append(f"{name}: tipo {actual_type}, esperado {type_name}")
        if bool(column["nullable"]) != nullable:
            problems.append(f"{name}: nullable={column['nullable']}, esperado {nullable}")
        actual_default = _norm_default(column["default"])
        if actual_default != default:
            problems.append(
                f"{name}: default {actual_default!r}, esperado {default!r}"
            )
    return problems


def _pk_mismatch(inspector: sa.Inspector, table: str) -> str | None:
    columns = inspector.get_pk_constraint(table).get("constrained_columns") or []
    if list(columns) != ["id"]:
        return f"PK {columns!r}, esperada ['id']"
    return None


def _unique_mismatches(
    inspector: sa.Inspector,
    table: str,
    expected: dict[str, tuple[str, ...]],
) -> list[str]:
    actual = {
        constraint.get("name"): tuple(constraint.get("column_names") or ())
        for constraint in inspector.get_unique_constraints(table)
    }
    problems: list[str] = []
    for name, columns in expected.items():
        if actual.get(name) != columns:
            problems.append(f"unique {name}: {actual.get(name)!r}, esperado {columns!r}")
    return problems


def _check_mismatches(
    inspector: sa.Inspector,
    table: str,
    expected: dict[str, str],
) -> list[str]:
    actual = {
        constraint.get("name"): _norm_sql(constraint.get("sqltext"))
        for constraint in inspector.get_check_constraints(table)
    }
    problems: list[str] = []
    for name, expression in expected.items():
        if actual.get(name) != _norm_sql(expression):
            problems.append(
                f"check {name}: {actual.get(name)!r}, esperado {_norm_sql(expression)!r}"
            )
    return problems


def _fk_set(inspector: sa.Inspector, table: str) -> set[tuple]:
    result: set[tuple] = set()
    for fk in inspector.get_foreign_keys(table):
        result.add(
            (
                tuple(fk.get("constrained_columns") or ()),
                fk.get("referred_table"),
                tuple(fk.get("referred_columns") or ()),
                (fk.get("options") or {}).get("ondelete"),
            )
        )
    return result


def _fk_mismatches(
    inspector: sa.Inspector,
    table: str,
    expected: set[tuple],
) -> list[str]:
    actual = _fk_set(inspector, table)
    if actual == expected:
        return []
    return [f"FKs {sorted(actual)!r}, esperadas {sorted(expected)!r}"]


def _index_map(inspector: sa.Inspector, table: str) -> dict[str, tuple[tuple[str, ...], bool]]:
    return {
        index.get("name"): (
            tuple(index.get("column_names") or ()),
            bool(index.get("unique")),
        )
        for index in inspector.get_indexes(table)
    }


def _index_mismatches(
    inspector: sa.Inspector,
    table: str,
    expected: dict[str, tuple[str, ...]],
) -> list[str]:
    actual = _index_map(inspector, table)
    problems: list[str] = []
    for name, columns in expected.items():
        if actual.get(name) != (columns, False):
            problems.append(f"índice {name}: {actual.get(name)!r}, esperado {columns!r}")
    return problems


def _sql_fragments_ok(table: str, fragments: tuple[str, ...]) -> bool:
    sql = _norm_sql(_table_sql(table))
    return all(_norm_sql(fragment) in sql for fragment in fragments)


def _abort(message: str, details: list[str] | None = None) -> None:
    lines = [message]
    if details:
        lines.extend(f"- {detail}" for detail in details[:20])
        if len(details) > 20:
            lines.append(f"- ... y {len(details) - 20} más")
    raise RuntimeError("\n".join(lines))


def _count(table: str) -> int:
    return int(
        op.get_bind()
        .execute(sa.text(f"SELECT COUNT(*) FROM {table}"))
        .scalar_one()
    )


def _non_null_count(table: str, column: str) -> int:
    return int(
        op.get_bind()
        .execute(
            sa.text(f'SELECT COUNT(*) FROM {table} WHERE "{column}" IS NOT NULL')
        )
        .scalar_one()
    )


def _plan_history(inspector: sa.Inspector) -> _Plan:
    if not _table_exists(inspector, _HISTORY):
        _abort("0010: falta mind_canvas_history; la base no está en 0009")

    actual_columns = {
        column["name"] for column in inspector.get_columns(_HISTORY)
    }
    missing = _HISTORY_REQUIRED - actual_columns
    if missing:
        _abort(
            "0010: mind_canvas_history no contiene columnas requeridas",
            sorted(missing),
        )

    rows = _count(_HISTORY)
    extras = actual_columns - set(_HISTORY_COLUMN_SPECS)
    if extras:
        if rows:
            populated = [
                (column, _non_null_count(_HISTORY, column))
                for column in sorted(extras)
            ]
            populated = [(column, count) for column, count in populated if count]
            if populated:
                _abort(
                    "0010: mind_canvas_history tiene columnas extra con datos; "
                    "no se descartan en silencio",
                    [f"{column}: {count} valores no nulos" for column, count in populated],
                )
        return _Plan("rebuild", reason="columnas extra vacías")

    problems = _column_mismatches(inspector, _HISTORY, _HISTORY_COLUMN_SPECS)
    pk_problem = _pk_mismatch(inspector, _HISTORY)
    if pk_problem:
        problems.append(pk_problem)
    problems.extend(_unique_mismatches(inspector, _HISTORY, _HISTORY_UNIQUES))
    problems.extend(_check_mismatches(inspector, _HISTORY, _HISTORY_CHECKS))
    problems.extend(_fk_mismatches(inspector, _HISTORY, _HISTORY_FKS))
    fragments = (
        "unique (canvas_id, sequence)",
        "unique (canvas_id, request_key)",
        "check (state in ('applied', 'undone', 'discarded'))",
        "foreign key (canvas_id) references mind_canvases (id) on delete cascade",
    )
    if not _sql_fragments_ok(_HISTORY, fragments):
        problems.append("sqlite_master no contiene las restricciones finales")

    if problems:
        return _Plan("rebuild", reason="; ".join(problems))

    index_problems = _index_mismatches(
        inspector,
        _HISTORY,
        {_HISTORY_INDEX[0]: _HISTORY_INDEX[1]},
    )
    if index_problems:
        return _Plan("index", reason="; ".join(index_problems))
    return _Plan("final")


def _prepare_history_rows(columns: set[str]) -> list[dict]:
    bind = op.get_bind()
    orphan_count = int(
        bind.execute(
            sa.text(
                "SELECT COUNT(*) FROM mind_canvas_history h "
                "LEFT JOIN mind_canvases c ON c.id = h.canvas_id "
                "WHERE c.id IS NULL"
            )
        ).scalar_one()
    )
    if orphan_count:
        _abort(
            "0010: mind_canvas_history contiene filas sin Canvas",
            [f"{orphan_count} filas huérfanas"],
        )

    raw_rows = list(
        bind.execute(
            sa.text(
                "SELECT * FROM mind_canvas_history "
                "ORDER BY canvas_id, created_at, id"
            )
        ).mappings()
    )

    has_sequence = "sequence" in columns
    has_state = "state" in columns
    has_undone_at = "undone_at" in columns
    has_request_key = "request_key" in columns
    has_inverse = "inverse_json" in columns

    sequences: defaultdict[str, int] = defaultdict(int)
    seen_sequences: defaultdict[str, set[int]] = defaultdict(set)
    seen_requests: set[tuple[str, str]] = set()
    prepared: list[dict] = []
    problems: list[str] = []

    for raw in raw_rows:
        row_id = raw["id"]
        canvas_id = raw["canvas_id"]
        snapshot = raw["snapshot_json"]
        if snapshot is None:
            problems.append(f"{row_id}: snapshot_json nulo")
            continue
        try:
            envelope = json.loads(snapshot)
        except (TypeError, json.JSONDecodeError):
            problems.append(f"{row_id}: snapshot_json no es JSON válido")
            continue
        if not isinstance(envelope, dict):
            envelope = {}

        stored_state = raw.get("state") if has_state else None
        if stored_state is not None and stored_state not in {
            "applied",
            "undone",
            "discarded",
        }:
            problems.append(f"{row_id}: state inválido {stored_state!r}")
            continue
        if envelope.get("discarded"):
            state = "discarded"
        elif envelope.get("undone"):
            state = "undone"
        elif stored_state in {"applied", "undone", "discarded"}:
            state = stored_state
        else:
            state = "applied"

        request_key = raw.get("request_key") if has_request_key else None
        if request_key == "":
            request_key = None
        if request_key is not None:
            pair = (canvas_id, str(request_key))
            if pair in seen_requests:
                problems.append(
                    f"{row_id}: request_key duplicado en Canvas {canvas_id}"
                )
                continue
            seen_requests.add(pair)

        if has_sequence:
            value = raw.get("sequence")
            if isinstance(value, bool):
                sequence = None
            elif isinstance(value, int):
                sequence = value
            elif isinstance(value, float) and value.is_integer():
                sequence = int(value)
            elif isinstance(value, str) and value.strip().isdigit():
                sequence = int(value.strip())
            else:
                sequence = None
            if sequence is None:
                problems.append(f"{row_id}: sequence no es entero ({value!r})")
                continue
            if sequence < 1:
                problems.append(f"{row_id}: sequence no positivo ({sequence})")
                continue
            if sequence in seen_sequences[canvas_id]:
                problems.append(
                    f"{row_id}: sequence duplicado en Canvas {canvas_id} ({sequence})"
                )
                continue
            seen_sequences[canvas_id].add(sequence)
        else:
            sequences[canvas_id] += 1
            sequence = sequences[canvas_id]

        prepared.append(
            {
                "id": row_id,
                "canvas_id": canvas_id,
                "sequence": sequence,
                "action_type": raw["action_type"],
                "snapshot_json": snapshot,
                "inverse_json": raw.get("inverse_json") if has_inverse else None,
                "request_key": request_key,
                "state": state,
                "undone_at": raw.get("undone_at") if has_undone_at else None,
                "created_at": raw["created_at"],
            }
        )

    if problems:
        _abort(
            "0010: mind_canvas_history contiene datos incompatibles; "
            "no se normalizan en silencio",
            problems,
        )
    return prepared


def _create_history_table(table: str) -> None:
    op.create_table(
        table,
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


def _rebuild_history(rows: list[dict]) -> None:
    inspector = _inspector()
    if _HISTORY_TMP in inspector.get_table_names():
        op.drop_table(_HISTORY_TMP)
    _create_history_table(_HISTORY_TMP)
    statement = sa.text(
        "INSERT INTO mind_canvas_history_0010 "
        "(id, canvas_id, sequence, action_type, snapshot_json, inverse_json, "
        "request_key, state, undone_at, created_at) VALUES "
        "(:id, :canvas_id, :sequence, :action_type, :snapshot_json, "
        ":inverse_json, :request_key, :state, :undone_at, :created_at)"
    )
    bind = op.get_bind()
    for row in rows:
        bind.execute(statement, row)
    copied = _count(_HISTORY_TMP)
    if copied != len(rows):
        _abort(
            "0010: el rebuild de history no preservó todas las filas",
            [f"esperadas {len(rows)}, copiadas {copied}"],
        )
    op.drop_table(_HISTORY)
    op.rename_table(_HISTORY_TMP, _HISTORY)
    op.create_index(
        _HISTORY_INDEX[0],
        _HISTORY,
        list(_HISTORY_INDEX[1]),
    )


def _plan_edges(inspector: sa.Inspector) -> _Plan:
    if not _table_exists(inspector, _EDGES):
        _abort("0010: falta mind_canvas_edges; la base no está en 0009")

    actual_columns = {column["name"] for column in inspector.get_columns(_EDGES)}
    rows = _count(_EDGES)
    extras = actual_columns - set(_EDGE_COLUMN_SPECS)

    if extras and rows:
        populated = [
            (column, _non_null_count(_EDGES, column))
            for column in sorted(extras)
        ]
        populated = [(column, count) for column, count in populated if count]
        if populated:
            ids = [
                str(value)
                for value in op.get_bind()
                .execute(sa.text(f"SELECT id FROM {_EDGES} ORDER BY id LIMIT 20"))
                .scalars()
            ]
            _abort(
                "0010: mind_canvas_edges contiene metadatos legacy que se "
                "perderían al reconstruir la tabla; exportá o transformá esas "
                "filas antes de reintentar",
                [
                    *[
                        f"{column}: {count} valores no nulos"
                        for column, count in populated
                    ],
                    f"IDs: {', '.join(ids)}",
                ],
            )

    missing = _EDGE_REQUIRED - actual_columns
    if missing:
        _abort(
            "0010: mind_canvas_edges no contiene columnas requeridas",
            sorted(missing),
        )

    if extras:
        return _Plan("rebuild", reason="columnas legacy vacías")

    problems = _column_mismatches(inspector, _EDGES, _EDGE_COLUMN_SPECS)
    pk_problem = _pk_mismatch(inspector, _EDGES)
    if pk_problem:
        problems.append(pk_problem)
    problems.extend(_unique_mismatches(inspector, _EDGES, _EDGE_UNIQUES))
    problems.extend(_check_mismatches(inspector, _EDGES, _EDGE_CHECKS))
    problems.extend(_fk_mismatches(inspector, _EDGES, _EDGE_FKS))
    fragments = (
        "unique (canvas_id, source_node_id, target_node_id)",
        "check (source_node_id < target_node_id)",
        "check (source_anchor between 0 and 7)",
        "check (target_anchor between 0 and 7)",
        "foreign key (canvas_id, source_node_id) references "
        "mind_canvas_nodes (canvas_id, id) on delete cascade",
        "foreign key (canvas_id, target_node_id) references "
        "mind_canvas_nodes (canvas_id, id) on delete cascade",
    )
    if not _sql_fragments_ok(_EDGES, fragments):
        problems.append("sqlite_master no contiene las restricciones finales")

    if problems:
        return _Plan("rebuild", reason="; ".join(problems))

    index_problems = _index_mismatches(inspector, _EDGES, _EDGE_INDEXES)
    if index_problems:
        return _Plan("index", reason="; ".join(index_problems))
    return _Plan("final")


def _prepare_edge_rows(columns: set[str]) -> list[dict]:
    bind = op.get_bind()
    node_membership = {
        (row["id"], row["canvas_id"])
        for row in bind.execute(
            sa.text("SELECT id, canvas_id FROM mind_canvas_nodes")
        ).mappings()
    }
    rows = list(
        bind.execute(
            sa.text(f"SELECT * FROM {_EDGES} ORDER BY created_at, id")
        ).mappings()
    )
    pairs: set[tuple[str, str, str]] = set()
    prepared: list[dict] = []
    problems: list[str] = []
    for raw in rows:
        edge_id = raw["id"]
        canvas_id = raw["canvas_id"]
        source = raw["source_node_id"]
        target = raw["target_node_id"]
        if source == target:
            problems.append(f"{edge_id}: self-loop")
            continue
        if (source, canvas_id) not in node_membership or (
            target,
            canvas_id,
        ) not in node_membership:
            problems.append(f"{edge_id}: extremo fuera del Canvas")
            continue

        source_anchor = raw.get("source_anchor") if "source_anchor" in columns else 0
        target_anchor = raw.get("target_anchor") if "target_anchor" in columns else 0
        try:
            source_anchor = 0 if source_anchor is None else int(source_anchor)
            target_anchor = 0 if target_anchor is None else int(target_anchor)
        except (TypeError, ValueError):
            problems.append(f"{edge_id}: anclaje no entero")
            continue
        if not (0 <= source_anchor <= 7 and 0 <= target_anchor <= 7):
            problems.append(f"{edge_id}: anclaje fuera de 0..7")
            continue

        if source > target:
            source, target = target, source
            source_anchor, target_anchor = target_anchor, source_anchor
        pair = (canvas_id, source, target)
        if pair in pairs:
            problems.append(f"{edge_id}: par no dirigido duplicado")
            continue
        pairs.add(pair)
        prepared.append(
            {
                "id": edge_id,
                "canvas_id": canvas_id,
                "source_node_id": source,
                "target_node_id": target,
                "source_anchor": source_anchor,
                "target_anchor": target_anchor,
                "created_at": raw["created_at"],
                "updated_at": raw["updated_at"],
            }
        )
    if problems:
        _abort(
            "0010: mind_canvas_edges contiene datos incompatibles; "
            "no se descartan ni normalizan en silencio",
            problems,
        )
    return prepared


def _create_edges_table(table: str) -> None:
    op.create_table(
        table,
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("canvas_id", sa.String(length=36), nullable=False),
        sa.Column("source_node_id", sa.String(length=36), nullable=False),
        sa.Column("target_node_id", sa.String(length=36), nullable=False),
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
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.Column("updated_at", sa.String(length=32), nullable=False),
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
        sa.CheckConstraint(
            "source_anchor BETWEEN 0 AND 7",
            name="ck_mind_canvas_edges_source_anchor",
        ),
        sa.CheckConstraint(
            "target_anchor BETWEEN 0 AND 7",
            name="ck_mind_canvas_edges_target_anchor",
        ),
    )


def _rebuild_edges(rows: list[dict]) -> None:
    inspector = _inspector()
    if _EDGES_TMP in inspector.get_table_names():
        op.drop_table(_EDGES_TMP)
    _create_edges_table(_EDGES_TMP)
    statement = sa.text(
        "INSERT INTO mind_canvas_edges_0010 "
        "(id, canvas_id, source_node_id, target_node_id, source_anchor, "
        "target_anchor, created_at, updated_at) VALUES "
        "(:id, :canvas_id, :source_node_id, :target_node_id, :source_anchor, "
        ":target_anchor, :created_at, :updated_at)"
    )
    bind = op.get_bind()
    for row in rows:
        bind.execute(statement, row)
    copied = _count(_EDGES_TMP)
    if copied != len(rows):
        _abort(
            "0010: el rebuild de edges no preservó todas las filas",
            [f"esperadas {len(rows)}, copiadas {copied}"],
        )
    op.drop_table(_EDGES)
    op.rename_table(_EDGES_TMP, _EDGES)
    for name, columns in _EDGE_INDEXES.items():
        op.create_index(name, _EDGES, list(columns))


def _plan_node_index(inspector: sa.Inspector) -> _Plan:
    if not _table_exists(inspector, _NODES):
        _abort("0010: falta mind_canvas_nodes; la base no está en 0009")
    indexes = _index_map(inspector, _NODES)
    current = indexes.get(_NODE_PAIR_INDEX)
    if current == (("canvas_id", "id"), True):
        return _Plan("final")
    if current is not None:
        _abort(
            "0010: existe un índice con el nombre "
            f"{_NODE_PAIR_INDEX} pero no es único sobre (canvas_id, id)"
        )
    for constraint in inspector.get_unique_constraints(_NODES):
        if constraint.get("name") == _NODE_PAIR_INDEX:
            columns = tuple(constraint.get("column_names") or ())
            if columns == ("canvas_id", "id"):
                return _Plan("final")
            _abort(
                "0010: existe una restricción con el nombre "
                f"{_NODE_PAIR_INDEX} pero con columnas {columns!r}"
            )
    duplicates = op.get_bind().execute(
        sa.text(
            "SELECT canvas_id, id, COUNT(*) FROM mind_canvas_nodes "
            "GROUP BY canvas_id, id HAVING COUNT(*) > 1 LIMIT 5"
        )
    ).fetchall()
    if duplicates:
        _abort(
            "0010: mind_canvas_nodes contiene pares (canvas_id, id) duplicados",
            [str(tuple(row)) for row in duplicates],
        )
    return _Plan("create")


def _ensure_index(
    table: str,
    name: str,
    columns: tuple[str, ...],
    *,
    unique: bool,
) -> None:
    inspector = _inspector()
    current = _index_map(inspector, table).get(name)
    if current == (columns, unique):
        return
    if current is not None:
        op.drop_index(name, table_name=table)
    op.create_index(name, table, list(columns), unique=unique)


def _assert_repaired_foreign_keys() -> None:
    bind = op.get_bind()
    for table in (_HISTORY, _EDGES):
        violations = bind.execute(
            sa.text(f"PRAGMA foreign_key_check({table})")
        ).fetchall()
        if violations:
            _abort(
                f"0010: {table} conserva violaciones de clave foránea",
                [str(tuple(row)) for row in violations[:20]],
            )


def upgrade() -> None:
    """Reconcile legacy Mind Canvas tables to the final schema."""
    inspector = _inspector()
    history_plan = _plan_history(inspector)
    edges_plan = _plan_edges(inspector)
    node_plan = _plan_node_index(inspector)

    if history_plan.action == "rebuild":
        history_rows = _prepare_history_rows(
            {
                column["name"]
                for column in inspector.get_columns(_HISTORY)
            }
        )
    else:
        history_rows = []

    if edges_plan.action == "rebuild":
        edge_rows = _prepare_edge_rows(
            {
                column["name"]
                for column in inspector.get_columns(_EDGES)
            }
        )
    else:
        edge_rows = []

    if node_plan.action == "create":
        op.create_index(
            _NODE_PAIR_INDEX,
            _NODES,
            ["canvas_id", "id"],
            unique=True,
        )

    if history_plan.action == "rebuild":
        _rebuild_history(history_rows)
    elif history_plan.action == "index":
        _ensure_index(
            _HISTORY,
            _HISTORY_INDEX[0],
            _HISTORY_INDEX[1],
            unique=False,
        )

    if edges_plan.action == "rebuild":
        _rebuild_edges(edge_rows)
    elif edges_plan.action == "index":
        for name, columns in _EDGE_INDEXES.items():
            _ensure_index(_EDGES, name, columns, unique=False)

    _assert_repaired_foreign_keys()


def downgrade() -> None:
    """Intentionally do not revert the repair.

    Revision 0009 already expects the final schema. Removing sequence/state/
    undone_at would destroy information and break the runtime; a real rollback
    is a verified SQLite backup. Alembic only moves the version stamp back.
    """
