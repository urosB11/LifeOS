"""Servicio de exportación, importación y backup de datos.

Exportación JSON versionada independiente del ORM (FR-DATA-03) y backup
SQLite consistente mediante ``sqlite3.Connection.backup`` (FR-DATA-04).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select

from app.db.activity import ActivityEvent
from app.db.session import engine
from app.modules.dashboard.models import WidgetPreference
from app.modules.dashboard.repository import UserPreferenceRepository
from app.modules.habits.models import Habit, HabitEntry
from app.modules.mind.models import (
    MindCanvas,
    MindCanvasEdge,
    MindCanvasHistory,
    MindCanvasNode,
    MindSpace,
    MindSpaceNote,
)
from app.modules.notes.models import Note, NoteProjectLink, NoteTag, NoteTaskLink, Tag
from app.modules.projects.models import Project
from app.modules.tasks.models import Task

EXPORT_FORMAT_VERSION = 2
SUPPORTED_IMPORT_VERSIONS = {1, EXPORT_FORMAT_VERSION}
MAX_IMPORT_BYTES = 10 * 1024 * 1024
MAX_ROWS_PER_TABLE = 100_000


def _row_dict(row) -> dict[str, Any]:
    return {column.name: getattr(row, column.name) for column in row.__table__.columns}


def build_export(db) -> dict[str, Any]:
    """Construye la exportación JSON versionada con todas las tablas de dominio."""
    exported_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    def list_table(model) -> list[dict[str, Any]]:
        return [_row_dict(r) for r in db.execute(select(model)).scalars().all()]

    return {
        "format_version": EXPORT_FORMAT_VERSION,
        "exported_at": exported_at,
        "projects": list_table(Project),
        "tasks": list_table(Task),
        "notes": list_table(Note),
        "note_project_links": list_table(NoteProjectLink),
        "note_task_links": list_table(NoteTaskLink),
        "tags": list_table(Tag),
        "note_tags": list_table(NoteTag),
        "habits": list_table(Habit),
        "habit_entries": list_table(HabitEntry),
        "mind_spaces": list_table(MindSpace),
        "mind_canvases": list_table(MindCanvas),
        "mind_space_notes": list_table(MindSpaceNote),
        "mind_canvas_nodes": list_table(MindCanvasNode),
        "mind_canvas_edges": list_table(MindCanvasEdge),
        "mind_canvas_history": list_table(MindCanvasHistory),
        "widget_preferences": list_table(WidgetPreference),
        "user_preferences": [
            {"key": p.key, "value": p.value, "updated_at": p.updated_at}
            for p in UserPreferenceRepository(db).list()
        ],
        "activity_events": list_table(ActivityEvent),
    }


def export_json_payload(db) -> str:
    """Serializa la exportación a JSON con IDs y relaciones conservados."""
    data = build_export(db)
    return json.dumps(data, ensure_ascii=False, indent=2)


def backup_sqlite_to_file(dest_path: str) -> None:
    """Crea una copia consistente de la base SQLite usando la API de backup.

    No copia el archivo directamente mientras hay escrituras activas.
    """
    source = sqlite3.connect(engine.url.database)
    try:
        dest = sqlite3.connect(dest_path)
        try:
            source.backup(dest)
        finally:
            dest.close()
    finally:
        source.close()


def validate_sqlite_file(path: str) -> None:
    """Valida que el archivo se abra y pase las comprobaciones SQLite."""
    conn = sqlite3.connect(path)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise ValueError(f"integrity_check falló: {result}")
        conn.execute("PRAGMA foreign_keys = ON")
        violations = conn.execute("PRAGMA foreign_key_check").fetchall()
        if violations:
            raise ValueError(
                f"foreign_key_check encontró {len(violations)} violaciones"
            )
    finally:
        conn.close()


def _import_tables() -> list[tuple[str, Any]]:
    """Orden de inserción que respeta todas las FK del export."""
    return [
        ("projects", Project),
        ("tasks", Task),
        ("tags", Tag),
        ("notes", Note),
        ("note_project_links", NoteProjectLink),
        ("note_task_links", NoteTaskLink),
        ("note_tags", NoteTag),
        ("habits", Habit),
        ("habit_entries", HabitEntry),
        ("mind_spaces", MindSpace),
        ("mind_canvases", MindCanvas),
        ("mind_space_notes", MindSpaceNote),
        ("mind_canvas_nodes", MindCanvasNode),
        ("mind_canvas_edges", MindCanvasEdge),
        ("mind_canvas_history", MindCanvasHistory),
        ("widget_preferences", WidgetPreference),
        ("activity_events", ActivityEvent),
    ]


def _validate_history_row(row: dict[str, Any], index: int) -> None:
    """Valida la semántica mínima de una entrada del historial del Canvas."""
    sequence = row.get("sequence")
    if type(sequence) is not int or sequence < 1:
        raise ValueError(f"mind_canvas_history[{index}].sequence debe ser un entero positivo")

    action_type = row.get("action_type")
    if not isinstance(action_type, str) or not action_type.strip() or len(action_type) > 30:
        raise ValueError(
            f"mind_canvas_history[{index}].action_type no es válido"
        )

    state = row.get("state")
    if state not in {"applied", "undone", "discarded"}:
        raise ValueError(
            f"mind_canvas_history[{index}].state debe ser applied, undone o discarded"
        )

    request_key = row.get("request_key")
    if request_key is not None and (
        not isinstance(request_key, str)
        or not request_key
        or len(request_key) > 64
    ):
        raise ValueError(
            f"mind_canvas_history[{index}].request_key no es válido"
        )

    for field in ("snapshot_json", "inverse_json"):
        payload = row.get(field)
        if payload is None and field == "inverse_json":
            continue
        if not isinstance(payload, str):
            raise ValueError(
                f"mind_canvas_history[{index}].{field} debe ser texto JSON"
            )
        try:
            envelope = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"mind_canvas_history[{index}].{field} no contiene JSON válido"
            ) from exc
        if not isinstance(envelope, dict):
            raise ValueError(
                f"mind_canvas_history[{index}].{field} debe contener un objeto JSON"
            )


def _validate_import_data(data: Any) -> tuple[int, list[tuple[str, Any]]]:
    """Valida la estructura completa antes de modificar la base."""
    if not isinstance(data, dict):
        raise ValueError("El payload importado debe ser un objeto JSON")

    fmt = data.get("format_version")
    if fmt not in SUPPORTED_IMPORT_VERSIONS:
        supported = ", ".join(str(value) for value in sorted(SUPPORTED_IMPORT_VERSIONS))
        raise ValueError(
            f"Formato no soportado: {fmt}. Formatos soportados: {supported}"
        )

    tables = _import_tables()
    allowed_top_level = {
        "format_version",
        "exported_at",
        "user_preferences",
        *(key for key, _model in tables),
    }
    unknown_top_level = set(data) - allowed_top_level
    if unknown_top_level:
        raise ValueError(
            "Campos desconocidos en el payload: "
            + ", ".join(sorted(unknown_top_level))
        )

    for key, model in tables:
        if key not in data:
            continue
        rows = data[key]
        if not isinstance(rows, list):
            raise ValueError(f"{key} debe ser una lista")
        if len(rows) > MAX_ROWS_PER_TABLE:
            raise ValueError(f"{key} supera el límite de {MAX_ROWS_PER_TABLE} filas")

        allowed_columns = {column.name for column in model.__table__.columns}
        primary_key = {column.name for column in model.__table__.primary_key.columns}
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise ValueError(f"{key}[{index}] debe ser un objeto")
            unknown_columns = set(row) - allowed_columns
            if unknown_columns:
                raise ValueError(
                    f"{key}[{index}] contiene campos desconocidos: "
                    + ", ".join(sorted(unknown_columns))
                )
            missing_primary_key = primary_key - set(row)
            if missing_primary_key:
                raise ValueError(
                    f"{key}[{index}] no contiene la clave primaria "
                    + ", ".join(sorted(missing_primary_key))
                )
            if fmt == EXPORT_FORMAT_VERSION:
                missing_columns = allowed_columns - set(row)
                if missing_columns:
                    raise ValueError(
                        f"{key}[{index}] no contiene los campos obligatorios: "
                        + ", ".join(sorted(missing_columns))
                    )
            if key == "mind_canvas_history":
                _validate_history_row(row, index)

    if "user_preferences" in data:
        preferences = data["user_preferences"]
        if not isinstance(preferences, list):
            raise ValueError("user_preferences debe ser una lista")
        if len(preferences) > MAX_ROWS_PER_TABLE:
            raise ValueError("user_preferences supera el límite de filas")
        for index, preference in enumerate(preferences):
            if not isinstance(preference, dict):
                raise ValueError(f"user_preferences[{index}] debe ser un objeto")
            unknown = set(preference) - {"key", "value", "updated_at"}
            if unknown:
                raise ValueError(
                    f"user_preferences[{index}] contiene campos desconocidos: "
                    + ", ".join(sorted(unknown))
                )
            if not preference.get("key") or "value" not in preference:
                raise ValueError(
                    f"user_preferences[{index}] requiere key y value"
                )

    return fmt, tables


def import_json_payload(db, payload: str) -> dict:
    """Importa un JSON de exportación mediante merge idempotente por PK.

    La validación completa ocurre antes de insertar. La transacción permanece
    bajo control de ``get_db``: un error revierte todos los cambios.
    """
    if len(payload.encode("utf-8")) > MAX_IMPORT_BYTES:
        raise ValueError("El payload importado supera el tamaño máximo permitido")

    try:
        data = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON inválido: {exc.msg}") from exc

    fmt, tables = _validate_import_data(data)
    inserted = 0
    skipped = 0

    # El savepoint mantiene la importación atómica incluso cuando la API usa
    # una sesión compartida: un IntegrityError revierte solo este payload y la
    # sesión queda utilizable para responder con un error explícito.
    with db.begin_nested():
        for key, model in tables:
            if key not in data:
                continue
            for row_data in data[key]:
                primary_key = [
                    column.name for column in model.__table__.primary_key.columns
                ]
                primary_key_values = tuple(row_data[column] for column in primary_key)
                existing = db.get(
                    model,
                    primary_key_values[0]
                    if len(primary_key_values) == 1
                    else primary_key_values,
                )
                if existing is not None:
                    skipped += 1
                    continue
                db.add(model(**row_data))
                inserted += 1
            db.flush()

        if "user_preferences" in data:
            repo = UserPreferenceRepository(db)
            for preference in data["user_preferences"]:
                existing = repo.get(preference["key"])
                if existing is not None:
                    skipped += 1
                    continue
                repo.upsert(preference["key"], preference["value"])
                inserted += 1

    return {"inserted": inserted, "skipped": skipped, "format_version": fmt}
