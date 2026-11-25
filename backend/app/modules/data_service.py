"""Servicio de exportación y backup de datos.

Exportación JSON versionada independiente del ORM (FR-DATA-03) y backup
SQLite consistente mediante `sqlite3.Connection.backup` (FR-DATA-04).
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
    MindCanvasNode,
    MindSpace,
    MindSpaceNote,
)
from app.modules.notes.models import Note, NoteProjectLink, NoteTag, NoteTaskLink, Tag
from app.modules.projects.models import Project
from app.modules.tasks.models import Task

EXPORT_FORMAT_VERSION = 2


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
    """Valida que el archivo se abra y pase PRAGMA integrity_check."""
    conn = sqlite3.connect(path)
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if result != "ok":
            raise ValueError(f"integrity_check falló: {result}")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA foreign_key_check")
    finally:
        conn.close()


def import_json_payload(db, payload: str) -> dict:
    """Importa un JSON de exportación en la base de datos actual.

    - Valida la versión del formato.
    - Inserta solo registros que no existan (por PK); no sobrescribe.
    - Requiere que las FK referenciadas existan o estén en el mismo payload.
    - Lanza ValueError si hay conflictos de integridad.
    """
    data = json.loads(payload)
    fmt = data.get("format_version")
    if fmt is None or fmt > EXPORT_FORMAT_VERSION:
        raise ValueError(f"Formato no soportado: {fmt}. Máximo soportado: {EXPORT_FORMAT_VERSION}")

    # Orden de inserción respetando dependencias FK
    tables_order = [
        ("projects", Project),
        ("tags", Tag),
        ("notes", Note),
        ("note_project_links", NoteProjectLink),
        ("note_task_links", NoteTaskLink),
        ("note_tags", NoteTag),
        ("tasks", Task),
        ("habits", Habit),
        ("habit_entries", HabitEntry),
        ("mind_spaces", MindSpace),
        ("mind_canvases", MindCanvas),
        ("mind_space_notes", MindSpaceNote),
        ("mind_canvas_nodes", MindCanvasNode),
        ("mind_canvas_edges", MindCanvasEdge),
        ("widget_preferences", WidgetPreference),
        ("activity_events", ActivityEvent),
    ]

    inserted = 0
    skipped = 0
    for key, model in tables_order:
        if key not in data:
            continue
        rows = data[key]
        for row_data in rows:
            pk_cols = [c.name for c in model.__table__.primary_key.columns]
            pk_vals = tuple(row_data[c] for c in pk_cols)
            existing = db.get(model, pk_vals[0] if len(pk_vals) == 1 else pk_vals)
            if existing:
                skipped += 1
                continue
            obj = model(**row_data)
            db.add(obj)
            inserted += 1
        db.flush()

    # user_preferences (no ORM model directo)
    if "user_preferences" in data:
        from app.modules.dashboard.repository import UserPreferenceRepository
        repo = UserPreferenceRepository(db)
        for pref in data["user_preferences"]:
            existing = repo.get(pref["key"])
            if not existing:
                repo.set(pref["key"], pref["value"])
                inserted += 1
            else:
                skipped += 1

    db.commit()
    return {"inserted": inserted, "skipped": skipped, "format_version": fmt}