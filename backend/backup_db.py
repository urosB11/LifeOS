"""Create and verify a consistent SQLite backup for Life OS.

The backup uses :meth:`sqlite3.Connection.backup`, which reads a consistent
snapshot and includes committed WAL frames. Copying only the main database
file while the application is running is not safe.

Examples::

    python backup_db.py
    python backup_db.py --source "%LOCALAPPDATA%\\LifeOS\\lifeos.db"
    python backup_db.py --destination D:\\Backups\\lifeos-20261127.db

The destination defaults to ``<data-dir>/backups/lifeos-YYYYMMDD-HHMMSS.db``.
Backups contain personal data: keep them outside the repository, restrict
access, and delete them according to the retention policy in SECURITY.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

REPO_ROOT = Path(__file__).resolve().parents[1]


class BackupError(RuntimeError):
    """A backup could not be created or verified."""


def default_data_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA")
        if not base:
            raise BackupError("LOCALAPPDATA no está definido")
        return Path(base) / "LifeOS"
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "LifeOS"
    base = os.environ.get("XDG_DATA_HOME")
    if base:
        return Path(base) / "life-os"
    return Path.home() / ".local" / "share" / "life-os"


def database_path_from_url(url: str) -> Path:
    value = url.strip()
    if value.startswith("sqlite:///"):
        value = value[len("sqlite:///") :]
    elif value.startswith("sqlite://"):
        value = value[len("sqlite://") :]
    elif "://" in value:
        raise BackupError(f"URL de base no soportada: {url}")
    return Path(unquote(value)).expanduser()


def resolve_source(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    url = os.environ.get("LIFEOS_DATABASE_URL")
    if url:
        return database_path_from_url(url).resolve()
    data_dir = os.environ.get("LIFEOS_DATA_DIR")
    base = Path(data_dir).expanduser().resolve() if data_dir else default_data_dir()
    return (base / "lifeos.db").resolve()


def resolve_destination(source: Path, explicit: str | None) -> Path:
    if explicit:
        destination = Path(explicit).expanduser().resolve()
    else:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        destination = (source.parent / "backups" / f"lifeos-{stamp}.db").resolve()

    try:
        destination.relative_to(REPO_ROOT)
    except ValueError:
        pass
    else:
        raise BackupError(
            "El backup no puede guardarse dentro del repositorio: "
            f"{destination}"
        )
    if destination == source:
        raise BackupError("El destino del backup no puede ser la base de origen")
    if destination.exists():
        raise BackupError(f"El destino ya existe; no se sobrescribe: {destination}")
    return destination


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def table_names(conn: sqlite3.Connection) -> list[str]:
    return [
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
    ]


def table_counts(conn: sqlite3.Connection) -> dict[str, int]:
    counts: dict[str, int] = {}
    for name in table_names(conn):
        quoted = '"' + name.replace('"', '""') + '"'
        counts[name] = int(conn.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0])
    return counts


def alembic_versions(conn: sqlite3.Connection) -> list[str]:
    if "alembic_version" not in table_names(conn):
        return []
    return [
        str(row[0])
        for row in conn.execute(
            "SELECT version_num FROM alembic_version ORDER BY version_num"
        )
    ]


def check_integrity(conn: sqlite3.Connection) -> None:
    integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise BackupError(f"integrity_check del backup = {integrity!r}")


def foreign_key_violations(conn: sqlite3.Connection) -> list[tuple]:
    return list(conn.execute("PRAGMA foreign_key_check").fetchall())


def open_readonly(path: Path) -> sqlite3.Connection:
    uri = "file:" + path.as_posix() + "?mode=ro"
    return sqlite3.connect(uri, uri=True)


def create_backup(source: Path, destination: Path) -> None:
    if not source.is_file():
        raise BackupError(f"No existe la base de origen: {source}")
    destination.parent.mkdir(parents=True, exist_ok=True)

    src = sqlite3.connect(str(source), timeout=5.0)
    dst = sqlite3.connect(str(destination), timeout=5.0)
    try:
        src.execute("PRAGMA busy_timeout = 5000")
        src.execute("PRAGMA query_only = ON")
        src.backup(dst)
    finally:
        dst.close()
        src.close()


def verify_backup(source: Path, destination: Path) -> dict:
    source_conn = sqlite3.connect(str(source), timeout=5.0)
    source_conn.execute("PRAGMA busy_timeout = 5000")
    source_conn.execute("PRAGMA query_only = ON")
    backup_conn = open_readonly(destination)
    try:
        check_integrity(backup_conn)
        violations = foreign_key_violations(backup_conn)
        source_counts = table_counts(source_conn)
        backup_counts = table_counts(backup_conn)
        source_versions = alembic_versions(source_conn)
        backup_versions = alembic_versions(backup_conn)
    finally:
        backup_conn.close()
        source_conn.close()

    if violations:
        raise BackupError(
            "El backup contiene violaciones de clave foránea: "
            + json.dumps([list(row) for row in violations[:20]], ensure_ascii=False)
        )
    if source_counts != backup_counts:
        changed = {
            table: (source_counts.get(table), backup_counts.get(table))
            for table in sorted(set(source_counts) | set(backup_counts))
            if source_counts.get(table) != backup_counts.get(table)
        }
        raise BackupError(
            "Los conteos del backup no coinciden con el origen; "
            "detené la aplicación y reintentá: "
            + json.dumps(changed, ensure_ascii=False)
        )
    if source_versions != backup_versions:
        raise BackupError(
            "alembic_version no coincide: "
            f"origen={source_versions!r}, backup={backup_versions!r}"
        )

    return {
        "source": str(source),
        "backup": str(destination),
        "size_bytes": destination.stat().st_size,
        "sha256": sha256(destination),
        "alembic_version": backup_versions,
        "tables": len(backup_counts),
        "rows": sum(backup_counts.values()),
        "integrity_check": "ok",
        "foreign_key_violations": 0,
    }


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Crea y verifica un backup consistente de Life OS (SQLite)."
    )
    parser.add_argument("--source", help="Base de origen (por defecto la base de datos de Life OS)")
    parser.add_argument(
        "--destination",
        help="Archivo de backup (por defecto <data-dir>/backups/lifeos-YYYYMMDD-HHMMSS.db)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        source = resolve_source(args.source)
        destination = resolve_destination(source, args.destination)
        create_backup(source, destination)
        summary = verify_backup(source, destination)
    except (BackupError, OSError, sqlite3.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
