"""Verificación de migraciones (Fase 6): base vacía, desde 0004, downgrade/upgrade."""

import os
import sqlite3
import subprocess
import sys
import tempfile

DATA_DIR = tempfile.mkdtemp(prefix="lifeos_mig_")
ENV = {**os.environ, "LIFEOS_DATA_DIR": DATA_DIR}
DB_PATH = os.path.join(DATA_DIR, "lifeos.db")
ALEMBIC = os.path.join(os.path.dirname(sys.executable), "alembic.exe")


def run(*args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [ALEMBIC, *args], env=ENV, capture_output=True, text=True, cwd=os.path.dirname(__file__)
    )
    print(f"--- alembic {' '.join(args)} (rc={result.returncode}) ---")
    print(result.stdout.strip())
    print(result.stderr.strip())
    if result.returncode != 0:
        print(f"FAIL alembic {' '.join(args)}")
        sys.exit(1)
    print(f"OK alembic {' '.join(args)}")


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def tables() -> list[str]:
    conn = db()
    try:
        return sorted(
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        )
    finally:
        conn.close()


def check_integrity(label: str) -> None:
    conn = db()
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        fk = conn.execute("PRAGMA foreign_key_check").fetchall()
        assert integrity == "ok", f"{label}: integrity_check = {integrity}"
        assert not fk, f"{label}: foreign_key_check encontró {len(fk)} violaciones"
        print(f"OK {label}: integrity_check=ok, foreign_key_check=0")
    finally:
        conn.close()


# 1. Base vacía → upgrade head
run("upgrade", "head")
expected = {
    "activity_events",
    "alembic_version",
    "note_project_links",
    "note_tags",
    "note_task_links",
    "notes",
    "projects",
    "tags",
    "tasks",
    "user_preferences",
    "widget_preferences",
}
got = set(tables())
missing = expected - got
assert not missing, f"Faltan tablas: {missing}"
print(f"OK base vacía → head: {len(got)} tablas")
check_integrity("base vacía")

# 2. Datos sintéticos antes del downgrade
conn = db()
conn.execute(
    "INSERT INTO projects (id, name, status, created_at, updated_at) "
    "VALUES ('p1', 'Proyecto prueba', 'active', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
)
conn.execute(
    "INSERT INTO tasks (id, title, status, project_id, created_at, updated_at) "
    "VALUES ('t1', 'Tarea prueba', 'pending', 'p1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
)
conn.commit()
conn.close()
print("OK datos sintéticos insertados")

# 3. Downgrade a 0001 (versión previa de prueba) y re-upgrade
run("downgrade", "0001_initial_schema")
conn = db()
try:
    remaining = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "alembic_version" in remaining
    assert "projects" in remaining and "tasks" in remaining
    assert "notes" not in remaining, "0001 no debe tener notes"
    assert "widget_preferences" not in remaining, "0001 no debe tener widget_preferences"
    # Los datos de 0001 deben sobrevivir al downgrade
    rows = conn.execute("SELECT id, name FROM projects").fetchall()
    assert rows == [("p1", "Proyecto prueba")], f"Datos de 0001 alterados: {rows}"
finally:
    conn.close()
print("OK downgrade a 0001_initial_schema: solo tablas 0001 + datos intactos")

run("upgrade", "head")
conn = db()
try:
    rows = conn.execute("SELECT id, name FROM projects").fetchall()
    assert rows == [("p1", "Proyecto prueba")], f"Datos alterados tras re-upgrade: {rows}"
    task = conn.execute("SELECT project_id FROM tasks WHERE id='t1'").fetchone()
    assert task == ("p1",), f"FK alterada tras re-upgrade: {task}"
finally:
    conn.close()
print("OK re-upgrade a head: datos y FK intactos")
check_integrity("re-upgrade")

# 4. Verificación final: head == 0004_widget_boolean
conn = db()
try:
    version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
    assert version == "0004_widget_boolean", f"Versión esperada 0004_widget_boolean, obtenida {version}"
    print(f"OK alembic_version = {version}")
finally:
    conn.close()

print(f"\nTODAS LAS VERIFICACIONES PASARON (dir: {DATA_DIR})")
