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
from app.modules.notes.models import Note, NoteProjectLink, NoteTag, NoteTaskLink, Tag
from app.modules.projects.models import Project
from app.modules.tasks.models import Task

EXPORT_FORMAT_VERSION = 1


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
