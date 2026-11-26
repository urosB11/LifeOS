"""Verificación del grafo combinado de migraciones Evolution + Mind.

La verificación usa siempre bases temporales y comprueba tanto la rama de
widgets de Home como la rama de Mind Canvas, incluido el mergepoint.
"""

import os
import sqlite3
import subprocess
import sys
import tempfile

DATA_DIR = tempfile.mkdtemp(prefix="lifeos_mig_")
ENV = {**os.environ, "LIFEOS_DATA_DIR": DATA_DIR}
DB_PATH = os.path.join(DATA_DIR, "lifeos.db")
ALEMBIC = os.path.join(os.path.dirname(sys.executable), "alembic.exe")

LEGACY_DATA_DIR = tempfile.mkdtemp(prefix="lifeos_mig_legacy_")
LEGACY_ENV = {**os.environ, "LIFEOS_DATA_DIR": LEGACY_DATA_DIR}
LEGACY_DB_PATH = os.path.join(LEGACY_DATA_DIR, "lifeos.db")

HEAD = "0009_merge_evolution_mind"
PREV_COMMON = "0005_habits"
PREV_HABITS = "0004_widget_boolean"
PREV_MIND = "0006_mind"

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
    "mind_canvas_edges",
    "mind_canvas_history",
}
MIND_SCHEMA_OBJECTS = {
    "mind_canvas_nodes",
    "mind_canvas_edges",
    "mind_canvas_history",
    "uq_mind_canvas_nodes_canvas_id_id",
    "ix_mind_canvas_edges_canvas_source",
    "ix_mind_canvas_edges_canvas_target",
    "ix_mind_canvas_history_canvas_created",
}


def run_in(env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [ALEMBIC, *args],
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=os.path.dirname(__file__),
    )
    print(f"--- alembic {' '.join(args)} (rc={result.returncode}) ---")
    print(result.stdout.strip())
    print(result.stderr.strip())
    if result.returncode != 0:
        print(f"FAIL alembic {' '.join(args)}")
        sys.exit(1)
    print(f"OK alembic {' '.join(args)}")
    return result


def run(*args: str) -> subprocess.CompletedProcess:
    return run_in(ENV, *args)


def db(path: str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def tables(path: str = DB_PATH) -> set[str]:
    conn = db(path)
    try:
        return {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
    finally:
        conn.close()


def table_columns(table_name: str, path: str = DB_PATH) -> set[str]:
    conn = db(path)
    try:
        return {
            row[1]
            for row in conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
    finally:
        conn.close()


def table_sql(table_name: str, path: str = DB_PATH) -> str:
    conn = db(path)
    try:
        row = conn.execute(
            "SELECT sql FROM sqlite_master WHERE type='table' AND name=?",
            (table_name,),
        ).fetchone()
        assert row is not None, f"No existe la tabla {table_name}"
        return row[0] or ""
    finally:
        conn.close()


def check_integrity(label: str, path: str = DB_PATH) -> None:
    conn = db(path)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        foreign_keys = conn.execute("PRAGMA foreign_key_check").fetchall()
        assert integrity == "ok", f"{label}: integrity_check = {integrity}"
        assert not foreign_keys, (
            f"{label}: foreign_key_check encontro {len(foreign_keys)} violaciones"
        )
        print(f"OK {label}: integrity_check=ok, foreign_key_check=0")
    finally:
        conn.close()


def check_version(expected: str, path: str = DB_PATH) -> None:
    conn = db(path)
    try:
        version = conn.execute("SELECT version_num FROM alembic_version").fetchone()[0]
        assert version == expected, f"Version esperada {expected}, obtenida {version}"
        print(f"OK alembic_version = {version}")
    finally:
        conn.close()


def insert_core_data(path: str = DB_PATH) -> None:
    """Inserta datos sinteticos de las ramas base, habitos y widgets."""
    conn = db(path)
    conn.execute(
        "INSERT INTO projects (id, name, status, created_at, updated_at) "
        "VALUES ('p1', 'Proyecto prueba', 'active', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO tasks (id, title, status, project_id, created_at, updated_at) "
        "VALUES ('t1', 'Tarea prueba', 'pending', 'p1', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO habits (id, name, frequency_type, start_date, status, position, "
        "created_at, updated_at) VALUES ('h1', 'Habito prueba', 'daily', "
        "'2026-01-01', 'active', 0, '2026-01-01T00:00:00Z', "
        "'2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO habit_entries (id, habit_id, entry_date, status, created_at, "
        "updated_at) VALUES ('e1', 'h1', '2026-01-01', 'completed', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
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
    print("OK datos sinteticos base, habitos y widgets insertados")


def insert_mind_data(path: str = DB_PATH) -> None:
    """Inserta y valida el esquema de Mind Canvas."""
    conn = db(path)
    conn.execute(
        "INSERT INTO notes (id, title, content, created_at, updated_at) "
        "VALUES ('n1', 'Nota 1', 'Contenido 1', '2026-01-01T00:00:00Z', "
        "'2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO notes (id, title, content, created_at, updated_at) "
        "VALUES ('n2', 'Nota 2', 'Contenido 2', '2026-01-01T00:00:00Z', "
        "'2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_spaces (id, name, description, is_inbox, status, "
        "created_at, updated_at) VALUES ('s1', 'Inbox', NULL, 1, 'active', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_spaces (id, name, description, is_inbox, status, "
        "created_at, updated_at) VALUES ('s2', 'Otro Space', NULL, 0, 'active', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_canvases (id, space_id, title, description, status, "
        "created_at, updated_at) VALUES ('c1', 's1', 'Canvas prueba', NULL, "
        "'active', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_canvases (id, space_id, title, description, status, "
        "created_at, updated_at) VALUES ('c2', 's2', 'Canvas otro', NULL, "
        "'active', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.executemany(
        "INSERT INTO mind_space_notes (space_id, note_id, created_at) "
        "VALUES (?, ?, '2026-01-01T00:00:00Z')",
        [("s1", "n1"), ("s1", "n2")],
    )
    conn.executemany(
        "INSERT INTO mind_canvas_nodes (id, canvas_id, note_id, x, y, width, "
        "height, z_index, created_at, updated_at) VALUES (?, ?, ?, ?, ?, "
        "NULL, NULL, ?, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')",
        [
            ("m1", "c1", "n1", 12.5, 40.0, 0),
            ("m2", "c1", "n2", 100.0, 80.0, 1),
            ("m3", "c2", "n1", 0.0, 0.0, 0),
        ],
    )
    conn.execute(
        "INSERT INTO mind_canvas_edges (id, canvas_id, source_node_id, "
        "target_node_id, source_anchor, target_anchor, created_at, updated_at) "
        "VALUES ('e1', 'c1', 'm1', 'm2', 1, 2, "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_canvas_history (id, canvas_id, sequence, action_type, "
        "snapshot_json, inverse_json, request_key, state, undone_at, created_at) "
        "VALUES ('h1', 'c1', 1, 'move', '{}', NULL, 'request-1', "
        "'applied', NULL, '2026-01-01T00:00:00Z')"
    )

    try:
        conn.execute(
            "INSERT INTO mind_spaces (id, name, description, is_inbox, status, "
            "created_at, updated_at) VALUES ('s3', 'Otro Inbox', NULL, 1, "
            "'active', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
        )
    except sqlite3.IntegrityError as exc:
        assert "UNIQUE" in str(exc).upper(), f"Error inesperado: {exc}"
        print("OK indice unico parcial: segundo Inbox rechazado")
    else:
        raise AssertionError("El segundo Inbox no fue rechazado")

    try:
        conn.execute(
            "INSERT INTO mind_canvas_history (id, canvas_id, sequence, action_type, "
            "snapshot_json, request_key, state, undone_at, created_at) "
            "VALUES ('h2', 'c1', 2, 'move', '{}', 'request-1', "
            "'applied', NULL, '2026-01-02T00:00:00Z')"
        )
    except sqlite3.IntegrityError as exc:
        assert "UNIQUE" in str(exc).upper(), f"Error inesperado: {exc}"
        print("OK historial: request_key duplicado rechazado")
    else:
        raise AssertionError("El request_key duplicado no fue rechazado")

    try:
        conn.execute(
            "INSERT INTO mind_canvas_edges (id, canvas_id, source_node_id, "
            "target_node_id, source_anchor, target_anchor, created_at, updated_at) "
            "VALUES ('cross-edge', 'c1', 'm1', 'm3', 0, 0, "
            "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
        )
    except sqlite3.IntegrityError as exc:
        assert "FOREIGN KEY" in str(exc).upper(), f"Error inesperado: {exc}"
        print("OK FK compuesta: edge con Card de otro Canvas rechazada")
    else:
        raise AssertionError("La FK compuesta no impidio una edge entre Canvases")

    try:
        conn.execute(
            "INSERT INTO mind_canvas_edges (id, canvas_id, source_node_id, "
            "target_node_id, source_anchor, target_anchor, created_at, updated_at) "
            "VALUES ('bad-anchor', 'c1', 'm1', 'm2', 8, 0, "
            "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
        )
    except sqlite3.IntegrityError as exc:
        assert "CHECK" in str(exc).upper(), f"Error inesperado: {exc}"
        print("OK CHECK de anchors: valor fuera de rango rechazado")
    else:
        raise AssertionError("El CHECK de anchors no impidio un valor invalido")

    # La FK de Note no puede expressarse sobre un snapshot JSON. El servicio
    # de Notes purga antes el historial de los Canvases afectados; el esquema
    # solo garantiza las cascadas de nodos y edges.
    conn.execute("DELETE FROM mind_canvas_history WHERE canvas_id='c1'")
    conn.execute("DELETE FROM notes WHERE id='n1'")
    nodes = conn.execute("SELECT COUNT(*) FROM mind_canvas_nodes").fetchone()[0]
    edges = conn.execute("SELECT COUNT(*) FROM mind_canvas_edges").fetchone()[0]
    history = conn.execute("SELECT COUNT(*) FROM mind_canvas_history").fetchone()[0]
    assert nodes == 1, f"mind_canvas_nodes conservo {nodes} filas huerfanas"
    assert edges == 0, f"mind_canvas_edges conservo {edges} filas huerfanas"
    assert history == 0, "El historial afectado por la Note debe estar purgado"
    conn.commit()
    conn.close()
    print("OK Mind Canvas: cascadas, edges e historial validados")


def assert_core_data(path: str = DB_PATH) -> None:
    conn = db(path)
    try:
        rows = conn.execute("SELECT id, name FROM projects").fetchall()
        assert rows == [("p1", "Proyecto prueba")], f"Datos alterados: {rows}"
        task = conn.execute("SELECT project_id FROM tasks WHERE id='t1'").fetchone()
        assert task == ("p1",), f"FK alterada: {task}"
    finally:
        conn.close()


def assert_widget_preferences(path: str = DB_PATH) -> None:
    conn = db(path)
    try:
        rows = conn.execute(
            "SELECT widget_id, is_visible, position, column_span, row_span "
            "FROM widget_preferences"
        ).fetchall()
        preferences = {row[0]: row[1:] for row in rows}
        positions = {row[0]: row[2] for row in rows}
        assert positions == {
            "upcoming_tasks": 0,
            "quick_add_task": 1,
            "quick_add_note": 1,
            "active_projects": 2,
            "habits_today": 3,
            "habits_week": 4,
        }, f"Orden migrado inesperado: {positions}"
        assert preferences["active_projects"][0] == 0, "Visibilidad alterada"
        assert preferences["upcoming_tasks"][2:] == (4, 1), "Spans incorrectos"
        assert preferences["habits_week"][2:] == (6, 1), "Spans incorrectos"
    finally:
        conn.close()


def assert_final_mind_schema(label: str, path: str = DB_PATH) -> None:
    """Comprueba restricciones e indices que el ORM necesita para el runtime."""
    edge_sql = table_sql("mind_canvas_edges", path)
    history_sql = table_sql("mind_canvas_history", path)

    for constraint in (
        "uq_mind_canvas_edges_canvas_source_target",
        "ck_mind_canvas_edges_source_lt_target",
        "ck_mind_canvas_edges_source_anchor",
        "ck_mind_canvas_edges_target_anchor",
    ):
        assert constraint in edge_sql, f"{label}: falta {constraint}"
    for constraint in (
        "uq_mind_canvas_history_canvas_sequence",
        "uq_mind_canvas_history_canvas_request_key",
        "ck_mind_canvas_history_state",
    ):
        assert constraint in history_sql, f"{label}: falta {constraint}"

    conn = db(path)
    try:
        edge_columns = {
            row[1]: row
            for row in conn.execute("PRAGMA table_info(mind_canvas_edges)")
        }
        assert edge_columns["source_anchor"][2].upper() == "INTEGER"
        assert edge_columns["target_anchor"][2].upper() == "INTEGER"
        assert edge_columns["source_anchor"][3] == 1
        assert edge_columns["target_anchor"][3] == 1

        foreign_key_groups: dict[int, set[tuple[str, str]]] = {}
        for row in conn.execute("PRAGMA foreign_key_list(mind_canvas_edges)"):
            foreign_key_groups.setdefault(row[0], set()).add((row[3], row[4]))
        group_pairs = list(foreign_key_groups.values())
        assert {
            ("canvas_id", "canvas_id"),
            ("source_node_id", "id"),
        } in group_pairs, f"{label}: FK compuesta source incompleta: {group_pairs}"
        assert {
            ("canvas_id", "canvas_id"),
            ("target_node_id", "id"),
        } in group_pairs, f"{label}: FK compuesta target incompleta: {group_pairs}"

        node_indexes = {
            row[1]: row[2]
            for row in conn.execute("PRAGMA index_list(mind_canvas_nodes)")
        }
        assert node_indexes.get("uq_mind_canvas_nodes_canvas_id_id") == 1

        edge_indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(mind_canvas_edges)")
        }
        assert {
            "ix_mind_canvas_edges_canvas_source",
            "ix_mind_canvas_edges_canvas_target",
        } <= edge_indexes

        history_indexes = {
            row[1]
            for row in conn.execute("PRAGMA index_list(mind_canvas_history)")
        }
        assert "ix_mind_canvas_history_canvas_created" in history_indexes
    finally:
        conn.close()
    check_integrity(label, path)
    print(f"OK {label}: esquema final de Mind Canvas validado")


def mind_schema_signature(path: str) -> tuple[tuple[str, str, str, str], ...]:
    conn = db(path)
    try:
        placeholders = ", ".join("?" for _ in MIND_SCHEMA_OBJECTS)
        rows = conn.execute(
            "SELECT type, name, tbl_name, sql FROM sqlite_master "
            f"WHERE name IN ({placeholders}) ORDER BY type, name",
            tuple(sorted(MIND_SCHEMA_OBJECTS)),
        ).fetchall()
        return tuple(rows)
    finally:
        conn.close()


def prepare_legacy_schema() -> None:
    """Crea un esquema 0006/0007 legado con edges e history sin versionar."""
    run_in(LEGACY_ENV, "upgrade", PREV_MIND)
    conn = db(LEGACY_DB_PATH)
    conn.execute(
        "CREATE TABLE mind_canvas_edges ("
        "id VARCHAR(36) NOT NULL PRIMARY KEY, "
        "canvas_id VARCHAR(36) NOT NULL, "
        "source_node_id VARCHAR(36) NOT NULL, "
        "target_node_id VARCHAR(36) NOT NULL, "
        "source_anchor TEXT, "
        "target_anchor TEXT, "
        "created_at VARCHAR(32) NOT NULL, "
        "updated_at VARCHAR(32) NOT NULL, "
        "FOREIGN KEY(canvas_id) REFERENCES mind_canvases(id) ON DELETE CASCADE, "
        "FOREIGN KEY(source_node_id) REFERENCES mind_canvas_nodes(id) ON DELETE CASCADE, "
        "FOREIGN KEY(target_node_id) REFERENCES mind_canvas_nodes(id) ON DELETE CASCADE)"
    )
    conn.execute(
        "CREATE TABLE mind_canvas_history ("
        "id VARCHAR(36) NOT NULL PRIMARY KEY, "
        "canvas_id VARCHAR(36) NOT NULL, "
        "action_type VARCHAR(30) NOT NULL, "
        "snapshot_json TEXT NOT NULL, "
        "inverse_json TEXT, "
        "request_key VARCHAR(64), "
        "created_at VARCHAR(32) NOT NULL, "
        "FOREIGN KEY(canvas_id) REFERENCES mind_canvases(id) ON DELETE CASCADE)"
    )
    conn.execute(
        "CREATE INDEX ix_mind_canvas_history_canvas_created "
        "ON mind_canvas_history (canvas_id, created_at)"
    )
    conn.execute(
        "INSERT INTO notes (id, title, content, created_at, updated_at) "
        "VALUES ('legacy-n1', 'Nota legacy', 'Contenido', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO notes (id, title, content, created_at, updated_at) "
        "VALUES ('legacy-n2', 'Nota legacy 2', 'Contenido', "
        "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_spaces (id, name, description, is_inbox, status, "
        "created_at, updated_at) VALUES ('legacy-s1', 'Legacy Inbox', NULL, 1, "
        "'active', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_canvases (id, space_id, title, description, status, "
        "created_at, updated_at) VALUES ('legacy-c1', 'legacy-s1', 'Legacy Canvas', "
        "NULL, 'active', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.executemany(
        "INSERT INTO mind_canvas_nodes (id, canvas_id, note_id, x, y, width, "
        "height, z_index, created_at, updated_at) VALUES (?, 'legacy-c1', ?, "
        "0, 0, NULL, NULL, 0, '2026-01-01T00:00:00Z', "
        "'2026-01-01T00:00:00Z')",
        [("legacy-z1", "legacy-n1"), ("legacy-z2", "legacy-n2")],
    )
    conn.execute(
        "INSERT INTO mind_canvas_edges (id, canvas_id, source_node_id, "
        "target_node_id, source_anchor, target_anchor, created_at, updated_at) "
        "VALUES ('legacy-e1', 'legacy-c1', 'legacy-z2', 'legacy-z1', '3', "
        "'invalid', '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
    )
    conn.execute(
        "INSERT INTO mind_canvas_history (id, canvas_id, action_type, "
        "snapshot_json, inverse_json, request_key, created_at) "
        "VALUES ('legacy-h1', 'legacy-c1', 'move', '{}', NULL, "
        "'legacy-request', '2026-01-01T00:00:00Z')"
    )
    conn.commit()
    conn.close()
    print("OK esquema legado 0006/0007 preparado")


def assert_legacy_data_reconciled() -> None:
    conn = db(LEGACY_DB_PATH)
    try:
        edge = conn.execute(
            "SELECT source_node_id, target_node_id, source_anchor, target_anchor "
            "FROM mind_canvas_edges WHERE id='legacy-e1'"
        ).fetchone()
        assert edge == ("legacy-z1", "legacy-z2", 0, 3), (
            f"Edge legacy no reconciliada: {edge}"
        )
        history = conn.execute(
            "SELECT sequence, state, request_key FROM mind_canvas_history "
            "WHERE id='legacy-h1'"
        ).fetchone()
        assert history == (1, "applied", "legacy-request"), (
            f"Historial legacy no reconciliado: {history}"
        )
    finally:
        conn.close()
    print("OK datos legados de edges e historial reconciliados")


# 1. El grafo combinado debe publicar un unico HEAD.
heads = run("heads")
assert HEAD in heads.stdout, f"El grafo no expone {HEAD} como HEAD"

# 2. Base vacia -> mergepoint head.
run("upgrade", "head")
run("check")
missing = (BASE_TABLES | HABIT_TABLES | MIND_TABLES) - tables()
assert not missing, f"Faltan tablas: {missing}"
assert_final_mind_schema("base vacia")
check_version(HEAD)
print("OK base vacia -> head: Evolution + Mind disponibles")

# 3. El ancestro comun conserva ambas ramas y sus datos base.
run("downgrade", PREV_COMMON)
check_version(PREV_COMMON)
remaining = tables()
assert not (MIND_TABLES & remaining), f"Las tablas de Mind deben caer: {MIND_TABLES & remaining}"
assert HABIT_TABLES <= remaining, f"Faltan tablas de 0005: {HABIT_TABLES - remaining}"
assert "column_span" not in table_columns("widget_preferences")
assert "row_span" not in table_columns("widget_preferences")
check_integrity("tras downgrade al ancestro comun")

# 4. Datos sinteticos en 0005 y upgrade de ambas ramas.
insert_core_data()
run("upgrade", "head")
assert_widget_preferences()
insert_mind_data()
assert {"source_anchor", "target_anchor"} <= table_columns("mind_canvas_edges")
assert_final_mind_schema("upgrade con datos de ambas ramas")
check_version(HEAD)
print("OK upgrade 0005 -> head: widgets de Evolution y Canvas de Mind coexisten")

# 5. Downgrade al ancestro comun elimina Mind y spans, conserva datos base.
run("downgrade", PREV_COMMON)
check_version(PREV_COMMON)
remaining = tables()
assert not (MIND_TABLES & remaining), f"Las tablas de Mind deben caer: {MIND_TABLES & remaining}"
assert "column_span" not in table_columns("widget_preferences")
assert "row_span" not in table_columns("widget_preferences")
assert_core_data()
check_integrity("tras downgrade al ancestro comun")
print("OK downgrade al ancestro comun: ramas eliminadas y datos base intactos")

# 6. Re-upgrade: ambas ramas se recrean y el merge vuelve a head.
run("upgrade", "head")
assert_widget_preferences()
remaining = tables()
assert MIND_TABLES <= remaining, f"Faltan tablas de Mind: {MIND_TABLES - remaining}"
conn = db()
try:
    assert conn.execute("SELECT COUNT(*) FROM mind_canvas_nodes").fetchone()[0] == 0
finally:
    conn.close()
assert_final_mind_schema("re-upgrade de ambas ramas")
check_version(HEAD)
print("OK re-upgrade de ambas ramas: mergepoint unico")

# 7. Downgrade a 0004 elimina habitos, Mind y spans.
run("downgrade", PREV_HABITS)
check_version(PREV_HABITS)
remaining = tables()
assert not (HABIT_TABLES & remaining), "Las tablas de habitos deben caer"
assert not (MIND_TABLES & remaining), "Las tablas de Mind deben caer"
assert "column_span" not in table_columns("widget_preferences")
assert "row_span" not in table_columns("widget_preferences")
assert_core_data()
check_integrity("tras downgrade a 0004")
print("OK downgrade a 0004: Evolution y Mind eliminados, base intacta")

run("upgrade", "head")
assert_widget_preferences()
conn = db()
try:
    assert conn.execute("SELECT COUNT(*) FROM habit_entries").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM mind_canvas_nodes").fetchone()[0] == 0
finally:
    conn.close()
assert_final_mind_schema("re-upgrade desde 0004")
check_version(HEAD)
print("OK upgrade desde 0004 a head: ambas ramas restauradas")

# 8. Downgrade historico a 0001 y re-upgrade final.
run("downgrade", "0001_initial_schema")
remaining = tables()
assert "alembic_version" in remaining
assert "projects" in remaining and "tasks" in remaining
assert "notes" not in remaining
assert "widget_preferences" not in remaining
assert not (HABIT_TABLES & remaining)
assert not (MIND_TABLES & remaining)
check_version("0001_initial_schema")
check_integrity("tras downgrade a 0001")
print("OK downgrade a 0001: solo esquema y datos historicos")

run("upgrade", "head")
assert_core_data()
assert_final_mind_schema("re-upgrade final")
check_version(HEAD)
fresh_signature = mind_schema_signature(DB_PATH)
print("OK re-upgrade final: datos, FKs y esquema de Mind intactos")

# 9. Un esquema legado 0006/0007 converge al mismo esquema final.
prepare_legacy_schema()
run_in(LEGACY_ENV, "upgrade", "head")
run_in(LEGACY_ENV, "check")
assert_legacy_data_reconciled()
assert_final_mind_schema("upgrade desde esquema legado", LEGACY_DB_PATH)
legacy_signature = mind_schema_signature(LEGACY_DB_PATH)
assert legacy_signature == fresh_signature, (
    "El esquema legado no converge al esquema final de una base limpia"
)
check_version(HEAD, LEGACY_DB_PATH)
print("OK esquema legado -> head: mismo esquema que una base limpia")

# 10. El esquema legado tambien puede bajar y volver a levantarse.
run_in(LEGACY_ENV, "downgrade", PREV_COMMON)
assert not (MIND_TABLES & tables(LEGACY_DB_PATH))
check_integrity("downgrade desde esquema legado", LEGACY_DB_PATH)
run_in(LEGACY_ENV, "upgrade", "head")
assert_final_mind_schema("re-upgrade desde esquema legado", LEGACY_DB_PATH)
assert mind_schema_signature(LEGACY_DB_PATH) == fresh_signature
print("OK downgrade/re-upgrade del esquema legado")

print(f"\nTODAS LAS VERIFICACIONES PASARON (dir: {DATA_DIR})")
