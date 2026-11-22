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

HEAD = "0006_mind"
PREV = "0005_habits"

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
MIND_TABLES = {
    "mind_spaces",
    "mind_canvases",
    "mind_space_notes",
    "mind_canvas_nodes",
}


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
    # Mind (MIND-002): Space, Canvas, Note canónica, membresía y nodo visual.
    conn.execute(
        "INSERT INTO notes (id, title, content, created_at, updated_at) "
        "VALUES ('n1', 'Nota prueba', 'Contenido', '2026-01-01T00:00:00Z', "
        "'2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_spaces (id, name, description, is_inbox, status, "
        "created_at, updated_at) VALUES ('s1', 'Inbox', NULL, 1, 'active', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_canvases (id, space_id, title, description, status, "
        "created_at, updated_at) VALUES ('c1', 's1', 'Canvas prueba', NULL, "
        "'active', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_space_notes (space_id, note_id, created_at) "
        "VALUES ('s1', 'n1', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_canvas_nodes (id, canvas_id, note_id, x, y, width, "
        "height, z_index, created_at, updated_at) VALUES ('m1', 'c1', 'n1', "
        "12.5, 40.0, NULL, NULL, 0, '2026-01-01T00:00:00Z', "
        "'2026-01-01T00:00:00Z')"
    )
    # Índice único parcial: un segundo Inbox debe ser rechazado por la BD.
    try:
        conn.execute(
            "INSERT INTO mind_spaces (id, name, description, is_inbox, status, "
            "created_at, updated_at) VALUES ('s2', 'Otro Inbox', NULL, 1, "
            "'active', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
        )
    except sqlite3.IntegrityError as exc:
        assert "UNIQUE" in str(exc).upper(), f"Error inesperado: {exc}"
        print("OK índice único parcial: segundo Inbox rechazado")
    else:
        raise AssertionError("El segundo Inbox no fue rechazado")
    # Borrar la Note elimina sus referencias visuales (ON DELETE CASCADE).
    conn.execute("DELETE FROM notes WHERE id='n1'")
    nodes = conn.execute("SELECT COUNT(*) FROM mind_canvas_nodes").fetchone()[0]
    assert nodes == 0, f"mind_canvas_nodes conservó {nodes} filas huérfanas"
    print("OK ON DELETE CASCADE: borrar la Note elimina sus referencias Mind")
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
missing = (BASE_TABLES | HABIT_TABLES | MIND_TABLES) - got
assert not missing, f"Faltan tablas: {missing}"
print(f"OK base vacía → head: {len(got)} tablas")
check_integrity("base vacía")
check_version(HEAD)

# 2. Datos sintéticos (incluye hábitos y sus restricciones)
insert_sample_data()

# 3. Downgrade a 0005 (versión previa real) y re-upgrade a head
run("downgrade", PREV)
conn = db()
try:
    remaining = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert not (MIND_TABLES & remaining), f"Las tablas de Mind deben caer: {MIND_TABLES & remaining}"
    assert HABIT_TABLES <= remaining, f"Faltan tablas de 0005: {HABIT_TABLES - remaining}"
finally:
    conn.close()
check_integrity("tras downgrade a 0005")
check_version(PREV)
print("OK downgrade a 0005_habits: tablas de Mind eliminadas, 0005 intacta")

run("upgrade", "head")
assert_core_data()
conn = db()
try:
    assert tables() and (BASE_TABLES | HABIT_TABLES | MIND_TABLES) <= set(tables())
    # Los datos de hábitos vivían en 0005: sobreviven al ciclo
    n = conn.execute("SELECT COUNT(*) FROM habit_entries").fetchone()[0]
    assert n == 1, f"habit_entries debería conservar 1 fila, tiene {n}"
    # Las tablas de Mind vivían en 0006: se recrean vacías (esperado)
    n = conn.execute("SELECT COUNT(*) FROM mind_canvas_nodes").fetchone()[0]
    assert n == 0, f"mind_canvas_nodes debería estar vacía, tiene {n}"
finally:
    conn.close()
check_integrity("re-upgrade desde 0005")
check_version(HEAD)
print("OK upgrade desde 0005 a head: datos 0005 intactos y tablas de Mind creadas")

# 4. Downgrade a 0001 (versión histórica de prueba) y re-upgrade
run("downgrade", "0001_initial_schema")
conn = db()
try:
    remaining = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "alembic_version" in remaining
    assert "projects" in remaining and "tasks" in remaining
    assert "notes" not in remaining, "0001 no debe tener notes"
    assert "widget_preferences" not in remaining, "0001 no debe tener widget_preferences"
    assert "habits" not in remaining, "0001 no debe tener habits"
    assert not (MIND_TABLES & remaining), "0001 no debe tener tablas de Mind"
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
