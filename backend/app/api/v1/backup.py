"""Rutas API de backup y restauración de SQLite."""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException
from fastapi.background import BackgroundTasks
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.db.session import engine
from app.modules.data_service import backup_sqlite_to_file, validate_sqlite_file

router = APIRouter(tags=["backup"])

settings = get_settings()


def _backups_dir() -> Path:
    data_dir = Path(settings.data_dir)
    backups_dir = data_dir / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)
    return backups_dir


def _remove_temp(path: str) -> None:
    try:
        os.unlink(path)
    except OSError:
        pass


@router.get("/backup")
def backup_database(background_tasks: BackgroundTasks):
    """Descarga una copia consistente de la base SQLite (FR-DATA-04)."""
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        backup_sqlite_to_file(tmp_path)
        background_tasks.add_task(_remove_temp, tmp_path)
        return FileResponse(
            tmp_path,
            media_type="application/octet-stream",
            filename="lifeos-backup.db",
        )
    except Exception:
        _remove_temp(tmp_path)
        raise HTTPException(status_code=500, detail="Error creando backup")


@router.post("/backup")
def save_backup():
    """Guarda una copia consistente en el directorio de backups del usuario."""
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        backup_sqlite_to_file(tmp_path)
        dest = (
            _backups_dir()
            / f"lifeos-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        )
        shutil.move(tmp_path, dest)
        return {"backup_path": str(dest)}
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail="Error creando backup")


@router.post("/restore")
def restore_database(
    background_tasks: BackgroundTasks,
    file_body: bytes = Body(..., media_type="application/octet-stream"),
):
    """Restaura la base desde un backup SQLite enviado como cuerpo raw.

    Antes de reemplazar la base activa se crea un backup adicional y se
    valida la integridad de la copia restaurada (FR-DATA-05).
    """
    active_db = engine.url.database
    if not active_db or not os.path.exists(active_db):
        raise HTTPException(status_code=404, detail="Base de datos activa no encontrada")

    # Validar archivo subido (cuerpo raw)
    fd, tmp_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        with open(tmp_path, "wb") as f:
            f.write(file_body)
        validate_sqlite_file(tmp_path)
    except Exception as exc:
        _remove_temp(tmp_path)
        raise HTTPException(status_code=400, detail=f"Backup inválido: {exc}")

    # Backup de seguridad de la base actual antes de reemplazar
    safety_fd, safety_path = tempfile.mkstemp(suffix=".db")
    os.close(safety_fd)
    try:
        backup_sqlite_to_file(safety_path)
        shutil.move(tmp_path, active_db)
        # Descartar las conexiones del pool: siguen apuntando al archivo
        # reemplazado y leerían datos obsoletos. Al hacer dispose, la
        # siguiente conexión abre la base restaurada.
        engine.dispose()
    except Exception:
        _remove_temp(tmp_path)
        try:
            _remove_temp(safety_path)
        except OSError:
            pass
        raise HTTPException(status_code=500, detail="Error restaurando base de datos")

    try:
        os.unlink(safety_path)
    except OSError:
        pass

    return {
        "restored": True,
        "active_db": active_db,
    }
