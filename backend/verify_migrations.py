"""Verificación de migraciones (Fases 6-7): base vacía, desde 0004, downgrade/upgrade."""

import os
import sqlite3
import subprocess
import sys
import tempfile

DATA_DIR = tempfile.mkdtemp(prefix="lifeos_mig_")
ENV = {**os.environ, "LIFEOS_DATA_DIR": DATA_DIR}
DB_PATH = os.path.join(DATA_DIR, "lifeos.db")
ALEMBIC = os.path.join(os.path.dirname(sys.executable), "alembic.exe")

HEAD = "0006_home_widget_grid"
PREV_WIDGETS = "0005_habits"
PREV_HABITS = "0004_widget_boolean"

BASE_TABLES = {
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
HABIT_TABLES = {"habits", "habit_entries"}


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


def check_version(expected: str) -> None:
    conn = db()
    try:
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        assert version == expected, f"Versión esperada {expected}, obtenida {version}"
        print(f"OK alembic_version = {version}")
    finally:
        conn.close()


def insert_sample_data() -> None:
    """Datos sintéticos de todas las entidades (incluidas hábitos)."""
    conn = db()
    conn.execute(
        "INSERT INTO projects (id, name, status, created_at, updated_at) "
        "VALUES ('p1', 'Proyecto prueba', 'active', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO tasks (id, title, status, project_id, created_at, updated_at) "
        "VALUES ('t1', 'Tarea prueba', 'pending', 'p1', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO habits (id, name, frequency_type, start_date, status, position, "
        "created_at, updated_at) VALUES ('h1', 'Habito prueba', 'daily', '2026-01-01', "
        "'active', 0, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO habit_entries (id, habit_id, entry_date, status, created_at, updated_at) "
        "VALUES ('e1', 'h1', '2026-01-01', 'completed', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    # UNIQUE(habit_id, entry_date) debe rechazar un segundo registro del día
    try:
        conn.execute(
            "INSERT INTO habit_entries (id, habit_id, entry_date, status, created_at, updated_at) "
            "VALUES ('e2', 'h1', '2026-01-01', 'pending', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
        )
    except sqlite3.IntegrityError as exc:
        assert "UNIQUE" in str(exc).upper(), f"Error inesperado: {exc}"
        print("OK UNIQUE(habit_id, entry_date) rechaza el duplicado")
    else:
        raise AssertionError("El registro duplicado de hábito no fue rechazado")
    # FK RESTRICT: no se puede borrar un hábito con registros
    try:
        conn.execute("DELETE FROM habits WHERE id='h1'")
    except sqlite3.IntegrityError as exc:
        assert "FOREIGN KEY" in str(exc).upper(), f"Error inesperado: {exc}"
        print("OK FK RESTRICT: hábito con registros no se elimina")
    else:
        raise AssertionError("La FK RESTRICT de habits no impidió el borrado")
    conn.commit()
    conn.close()
    print("OK datos sintéticos insertados")


def assert_core_data() -> None:
    conn = db()
    try:
        rows = conn.execute("SELECT id, name FROM projects").fetchall()
        assert rows == [("p1", "Proyecto prueba")], f"Datos alterados: {rows}"
        task = conn.execute("SELECT project_id FROM tasks WHERE id='t1'").fetchone()
        assert task == ("p1",), f"FK alterada: {task}"
    finally:
        conn.close()


# 1. Base vacía → upgrade head
run("upgrade", "head")
got = set(tables())
missing = (BASE_TABLES | HABIT_TABLES) - got
assert not missing, f"Faltan tablas: {missing}"
print(f"OK base vacía → head: {len(got)} tablas")
check_integrity("base vacía")
check_version(HEAD)

# 2. Simular preferencias existentes bajo el esquema 0005 y migrarlas.
run("downgrade", PREV_WIDGETS)
check_version(PREV_WIDGETS)

# 3. Datos sintéticos (incluye hábitos y sus restricciones)
insert_sample_data()

conn = db()
conn.executemany(
    "INSERT INTO widget_preferences "
    "(widget_id, is_visible, position, config_json, updated_at) "
    "VALUES (?, ?, ?, NULL, '2026-01-01T00:00:00Z')",
    [
        ("upcoming_tasks", 1, 0),
        ("active_projects", 0, 1),
        ("quick_add_task", 1, 2),
        ("quick_add_note", 0, 3),
        ("habits_today", 1, 4),
        ("habits_week", 1, 5),
    ],
)
conn.commit()
conn.close()
print("OK preferencias de widgets de 0005 insertadas")

run("upgrade", "head")
conn = db()
try:
    rows = conn.execute(
        "SELECT widget_id, is_visible, position, column_span, row_span "
        "FROM widget_preferences"
    ).fetchall()
    positions = {row[0]: row[2] for row in rows}
    assert positions == {
        "upcoming_tasks": 0,
        "quick_add_task": 1,
        "quick_add_note": 1,
        "active_projects": 2,
        "habits_today": 3,
        "habits_week": 4,
    }, f"Orden migrado inesperado: {positions}"
    preferences = {row[0]: row[1:] for row in rows}
    assert preferences["active_projects"][0] == 0, "Visibilidad alterada"
    assert preferences["upcoming_tasks"][2:] == (4, 1), "Spans de tareas incorrectos"
    assert preferences["habits_week"][2:] == (6, 1), "Spans de semana incorrectos"
finally:
    conn.close()
print("OK 0005→0006: orden por zonas, visibilidad y spans preservados")
check_integrity("migración de preferencias de widgets")
check_version(HEAD)

# 4. Downgrade a 0005 conserva un orden determinista para captura rápida
run("downgrade", PREV_WIDGETS)
conn = db()
try:
    columns = {
        row[1] for row in conn.execute("PRAGMA table_info(widget_preferences)")
    }
    assert "column_span" not in columns and "row_span" not in columns
    legacy_positions = dict(
        conn.execute(
            "SELECT widget_id, position FROM widget_preferences"
        ).fetchall()
    )
    assert (
        legacy_positions["quick_add_task"] < legacy_positions["quick_add_note"]
    ), f"Orden de captura rápida no determinista: {legacy_positions}"
finally:
    conn.close()
check_version(PREV_WIDGETS)
print("OK downgrade a 0005: columnas de spans eliminadas y captura en orden")

run("upgrade", "head")
conn = db()
try:
    upgraded_spans = {
        row[0]: row[1:]
        for row in conn.execute(
            "SELECT widget_id, column_span, row_span FROM widget_preferences"
        ).fetchall()
    }
    assert upgraded_spans["quick_add_task"] == (2, 1)
    assert upgraded_spans["quick_add_note"] == (2, 1)
finally:
    conn.close()
check_version(HEAD)
print("OK re-upgrade a 0006: captura rápida recupera sus spans")

# 5. Downgrade a 0004 (versión previa real) y re-upgrade a head
run("downgrade", PREV_HABITS)
conn = db()
try:
    remaining = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "habits" not in remaining and "habit_entries" not in remaining
    assert BASE_TABLES <= remaining, f"Faltan tablas de 0004: {BASE_TABLES - remaining}"
finally:
    conn.close()
check_integrity("tras downgrade a 0004")
check_version(PREV_HABITS)
print("OK downgrade a 0004_widget_boolean: tablas de hábitos eliminadas, 0004 intacta")

run("upgrade", "head")
assert_core_data()
conn = db()
try:
    assert tables() and (BASE_TABLES | HABIT_TABLES) <= set(tables())
    # Los registros de hábitos vivían en 0005: se recrean vacías (esperado)
    n = conn.execute("SELECT COUNT(*) FROM habit_entries").fetchone()[0]
    assert n == 0, f"habit_entries debería estar vacía tras re-upgrade, tiene {n}"
finally:
    conn.close()
check_integrity("re-upgrade desde 0004")
check_version(HEAD)
print("OK upgrade desde 0004 a head: datos 0004 intactos y tablas de hábitos creadas")

# 6. Downgrade a 0001 (versión histórica de prueba) y re-upgrade
run("downgrade", "0001_initial_schema")
conn = db()
try:
    remaining = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "alembic_version" in remaining
    assert "projects" in remaining and "tasks" in remaining
    assert "notes" not in remaining, "0001 no debe tener notes"
    assert "widget_preferences" not in remaining, "0001 no debe tener widget_preferences"
    assert "habits" not in remaining, "0001 no debe tener habits"
    rows = conn.execute("SELECT id, name FROM projects").fetchall()
    assert rows == [("p1", "Proyecto prueba")], f"Datos de 0001 alterados: {rows}"
finally:
    conn.close()
print("OK downgrade a 0001_initial_schema: solo tablas 0001 + datos intactos")

run("upgrade", "head")
assert_core_data()
check_integrity("re-upgrade")
check_version(HEAD)
print("OK re-upgrade a head: datos y FK intactos")

print(f"\nTODAS LAS VERIFICACIONES PASARON (dir: {DATA_DIR})")
