"""Pruebas de backup y restauración de SQLite (Fase 5)."""

import os
import sqlite3

from app.modules.data_service import backup_sqlite_to_file, validate_sqlite_file


def test_backup_sqlite_to_file_creates_valid_copy(tmp_path):
    """El backup mediante API de SQLite crea una copia consistente y válida."""
    dest = tmp_path / "backup.db"
    backup_sqlite_to_file(str(dest))
    assert dest.exists()
    assert dest.stat().st_size > 0

    # La copia debe abrirse y pasar integrity_check
    validate_sqlite_file(str(dest))

    # Debe contener las mismas tablas que la base activa
    conn = sqlite3.connect(str(dest))
    try:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        ]
        for expected in [
            "projects",
            "tasks",
            "notes",
            "tags",
            "widget_preferences",
            "user_preferences",
            "activity_events",
        ]:
            assert expected in tables, f"Falta tabla {expected} en el backup"
    finally:
        conn.close()


def test_validate_sqlite_file_rejects_corrupt(tmp_path):
    """Un archivo no válido debe rechazarse en validate_sqlite_file."""
    corrupt = tmp_path / "corrupt.db"
    corrupt.write_bytes(b"esto no es una base de datos sqlite")
    try:
        validate_sqlite_file(str(corrupt))
        assert False, "Debería haber lanzado excepción"
    except Exception:
        pass


def test_backup_endpoint_returns_file(client):
    """GET /api/v1/backup debe devolver un archivo descargable."""
    response = client.get("/api/v1/backup")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert "lifeos-backup.db" in response.headers.get("content-disposition", "")
    assert len(response.content) > 0


def test_save_backup_endpoint(client):
    """POST /api/v1/backup debe guardar en el directorio de backups y devolver ruta."""
    response = client.post("/api/v1/backup")
    assert response.status_code == 200, response.text
    data = response.json()
    assert "backup_path" in data
    assert os.path.exists(data["backup_path"])
