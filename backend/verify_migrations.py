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

HEAD = "0010_repair_mind_canvas_schema"
PREV_COMMON = "0005_habits"
PREV_HABITS = "0004_widget_boolean"
PREV_MIND = "0006_mind"
PREV_MERGE = "0009_merge_evolution_mind"

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


def decode_output(data: bytes | None) -> str:
    if not data:
        return ""
    for encoding in ("utf-8", "cp1252", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def run_in(env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [ALEMBIC, *args],
        env=env,
        capture_output=True,
        cwd=os.path.dirname(__file__),
    )
    result.stdout = decode_output(result.stdout)
    result.stderr = decode_output(result.stderr)
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


def make_env(prefix: str) -> tuple[dict[str, str], str, str]:
    data_dir = tempfile.mkdtemp(prefix=prefix)
    env = {**os.environ, "LIFEOS_DATA_DIR": data_dir}
    return env, data_dir, os.path.join(data_dir, "lifeos.db")


def run_in_expect_failure(
    env: dict[str, str],
    *args: str,
    contains: str | None = None,
) -> subprocess.CompletedProcess:
    result = subprocess.run(
        [ALEMBIC, *args],
        env=env,
        capture_output=True,
        cwd=os.path.dirname(__file__),
    )
    result.stdout = decode_output(result.stdout)
    result.stderr = decode_output(result.stderr)
    print(f"--- alembic {' '.join(args)} (rc={result.returncode}, esperado fallo) ---")
    print(result.stdout.strip())
    print(result.stderr.strip())
    assert result.returncode != 0, f"Se esperaba fallo de alembic {' '.join(args)}"
    combined = result.stdout + "\n" + result.stderr
    if contains:
        assert contains in combined, (
            f"El error no contiene {contains!r}:\n{combined}"
        )
    print(f"OK fallo esperado de alembic {' '.join(args)}")
    return result


def schema_snapshot(path: str) -> tuple[tuple[str, str, str, str], ...]:
    conn = db(path)
    try:
        return tuple(
            conn.execute(
                "SELECT type, name, tbl_name, COALESCE(sql, '') "
                "FROM sqlite_master ORDER BY type, name"
            ).fetchall()
        )
    finally:
        conn.close()


def table_rows(path: str, query: str) -> list[tuple]:
    conn = db(path)
    try:
        return conn.execute(query).fetchall()
    finally:
        conn.close()


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
        legacy_edge_columns = {
            "edge_type",
            "style_json",
            "ai_suggested",
            "ai_confidence",
        }
        assert not (legacy_edge_columns & set(edge_columns)), (
            f"{label}: columnas legacy de edges presentes: "
            f"{legacy_edge_columns & set(edge_columns)}"
        )

        history_columns = {
            row[1]: row
            for row in conn.execute("PRAGMA table_info(mind_canvas_history)")
        }
        assert {
            "sequence",
            "state",
            "undone_at",
            "request_key",
        } <= set(history_columns), (
            f"{label}: faltan columnas finales de history: "
            f"{set(history_columns)}"
        )
        assert history_columns["sequence"][2].upper() == "INTEGER"
        assert history_columns["sequence"][3] == 1
        assert history_columns["state"][2].upper() == "VARCHAR(12)"
        assert history_columns["state"][3] == 1
        assert history_columns["state"][4] == "'applied'"
        assert history_columns["undone_at"][3] == 0

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

        history_fks = conn.execute(
            "PRAGMA foreign_key_list(mind_canvas_history)"
        ).fetchall()
        assert len(history_fks) == 1, f"{label}: FKs de history: {history_fks}"
        history_fk = history_fks[0]
        assert history_fk[2] == "mind_canvases", history_fk
        assert history_fk[3] == "canvas_id" and history_fk[4] == "id", history_fk
        assert str(history_fk[6]).upper() == "CASCADE", history_fk
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


def seed_mind_graph(conn: sqlite3.Connection) -> None:
    """Inserta Notes, Spaces, Canvases y nodos sin edges ni historial."""
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
        "INSERT INTO mind_canvas_nodes (id, canvas_id, note_id, x, y, width, "
        "height, z_index, created_at, updated_at) VALUES (?, ?, ?, ?, ?, "
        "NULL, NULL, ?, '2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')",
        [
            ("m1", "c1", "n1", 12.5, 40.0, 0),
            ("m2", "c1", "n2", 100.0, 80.0, 1),
            ("m3", "c2", "n1", 0.0, 0.0, 0),
        ],
    )
    conn.commit()


def create_legacy_history(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS mind_canvas_history")
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


def create_partial_history(conn: sqlite3.Connection) -> None:
    """Final columns without constraints, to test data aborts."""
    conn.execute("DROP TABLE IF EXISTS mind_canvas_history")
    conn.execute(
        "CREATE TABLE mind_canvas_history ("
        "id VARCHAR(36) NOT NULL PRIMARY KEY, "
        "canvas_id VARCHAR(36) NOT NULL, "
        "sequence INTEGER NOT NULL, "
        "action_type VARCHAR(30) NOT NULL, "
        "snapshot_json TEXT NOT NULL, "
        "inverse_json TEXT, "
        "request_key VARCHAR(64), "
        "state VARCHAR(12) NOT NULL DEFAULT 'applied', "
        "undone_at VARCHAR(32), "
        "created_at VARCHAR(32) NOT NULL)"
    )


def create_legacy_edges(
    conn: sqlite3.Connection,
    *,
    metadata: bool,
) -> None:
    conn.execute("DROP TABLE IF EXISTS mind_canvas_edges")
    columns = [
        "id VARCHAR(36) NOT NULL PRIMARY KEY",
        "canvas_id VARCHAR(36) NOT NULL",
        "source_node_id VARCHAR(36) NOT NULL",
        "target_node_id VARCHAR(36) NOT NULL",
        "source_anchor TEXT",
        "target_anchor TEXT",
        "created_at VARCHAR(32) NOT NULL",
        "updated_at VARCHAR(32) NOT NULL",
    ]
    if metadata:
        columns.extend(
            [
                "edge_type VARCHAR(20) NOT NULL",
                "style_json TEXT",
                "ai_suggested BOOLEAN NOT NULL DEFAULT 0",
                "ai_confidence FLOAT",
            ]
        )
    columns.extend(
        [
            "FOREIGN KEY(canvas_id) REFERENCES mind_canvases(id) ON DELETE CASCADE",
            "FOREIGN KEY(source_node_id) REFERENCES mind_canvas_nodes(id) "
            "ON DELETE CASCADE",
            "FOREIGN KEY(target_node_id) REFERENCES mind_canvas_nodes(id) "
            "ON DELETE CASCADE",
        ]
    )
    conn.execute("CREATE TABLE mind_canvas_edges (" + ", ".join(columns) + ")")


def create_partial_edges(conn: sqlite3.Connection) -> None:
    """Representable edge columns without constraints or metadata."""
    conn.execute("DROP TABLE IF EXISTS mind_canvas_edges")
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
        "FOREIGN KEY(source_node_id) REFERENCES mind_canvas_nodes(id) "
        "ON DELETE CASCADE, "
        "FOREIGN KEY(target_node_id) REFERENCES mind_canvas_nodes(id) "
        "ON DELETE CASCADE)"
    )


def create_0007_edges(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS mind_canvas_edges")
    conn.execute(
        "CREATE TABLE mind_canvas_edges ("
        "id VARCHAR(36) NOT NULL PRIMARY KEY, "
        "canvas_id VARCHAR(36) NOT NULL, "
        "source_node_id VARCHAR(36) NOT NULL, "
        "target_node_id VARCHAR(36) NOT NULL, "
        "created_at VARCHAR(32) NOT NULL, "
        "updated_at VARCHAR(32) NOT NULL, "
        "FOREIGN KEY(canvas_id) REFERENCES mind_canvases(id) ON DELETE CASCADE, "
        "FOREIGN KEY(source_node_id) REFERENCES mind_canvas_nodes(id) "
        "ON DELETE CASCADE, "
        "FOREIGN KEY(target_node_id) REFERENCES mind_canvas_nodes(id) "
        "ON DELETE CASCADE, "
        "UNIQUE(canvas_id, source_node_id, target_node_id), "
        "CHECK(source_node_id < target_node_id))"
    )


def prepare_repair_db(prefix: str) -> tuple[dict[str, str], str, str]:
    """Crea una base en 0008 con grafo Mind y sin edges/historial finales."""
    env, _data_dir, path = make_env(prefix)
    run_in(env, "upgrade", "0008_mind_canvas_history")
    conn = db(path)
    try:
        seed_mind_graph(conn)
    finally:
        conn.close()
    return env, _data_dir, path


def run_repair(env: dict[str, str], path: str) -> None:
    run_in(env, "stamp", PREV_MERGE)
    run_in(env, "upgrade", "head")
    check_version(HEAD, path)


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

# 11. Historial legacy con filas: secuencia, estado y claves se preservan.
history_env, _, history_path = prepare_repair_db("lifeos_mig_hist_")
conn = db(history_path)
create_legacy_history(conn)
conn.executemany(
    "INSERT INTO mind_canvas_history "
    "(id, canvas_id, action_type, snapshot_json, inverse_json, request_key, "
    "created_at) VALUES (?, ?, 'move', ?, ?, ?, ?)",
    [
        (
            "h1",
            "c1",
            '{"nodes": []}',
            '{"inverse": 1}',
            "r1",
            "2026-01-01T00:00:00Z",
        ),
        (
            "h2",
            "c1",
            '{"undone": true}',
            None,
            "r2",
            "2026-01-01T00:00:00Z",
        ),
        (
            "h3",
            "c2",
            '{"discarded": true}',
            None,
            "r3",
            "2025-12-31T00:00:00Z",
        ),
        (
            "h4",
            "c2",
            "{}",
            None,
            None,
            "2026-01-02T00:00:00Z",
        ),
    ],
)
conn.commit()
conn.close()
run_repair(history_env, history_path)
history_rows = table_rows(
    history_path,
    "SELECT id, canvas_id, sequence, state, request_key, inverse_json, "
    "undone_at, created_at FROM mind_canvas_history "
    "ORDER BY canvas_id, sequence",
)
assert history_rows == [
    ("h1", "c1", 1, "applied", "r1", '{"inverse": 1}', None, "2026-01-01T00:00:00Z"),
    ("h2", "c1", 2, "undone", "r2", None, None, "2026-01-01T00:00:00Z"),
    ("h3", "c2", 1, "discarded", "r3", None, None, "2025-12-31T00:00:00Z"),
    ("h4", "c2", 2, "applied", None, None, None, "2026-01-02T00:00:00Z"),
], f"Historial legacy alterado: {history_rows}"
assert_final_mind_schema("historial legacy preservado", history_path)
print("OK historial legacy: filas, secuencias y estados preservados")

# 12. Aborto de historial con request_key duplicado.
dup_env, _, dup_path = prepare_repair_db("lifeos_mig_hist_dup_")
conn = db(dup_path)
create_legacy_history(conn)
conn.executemany(
    "INSERT INTO mind_canvas_history "
    "(id, canvas_id, action_type, snapshot_json, request_key, created_at) "
    "VALUES (?, 'c1', 'move', '{}', 'same-key', '2026-01-01T00:00:00Z')",
    [("dup-1",), ("dup-2",)],
)
conn.commit()
conn.close()
run_in(dup_env, "stamp", PREV_MERGE)
before = schema_snapshot(dup_path)
run_in_expect_failure(
    dup_env,
    "upgrade",
    "head",
    contains="request_key duplicado",
)
assert schema_snapshot(dup_path) == before, "El aborto de history modificó el esquema"
check_version(PREV_MERGE, dup_path)
print("OK aborto: request_key duplicado no modifica el esquema")

# 13. Aborto de historial con JSON inválido.
json_env, _, json_path = prepare_repair_db("lifeos_mig_hist_json_")
conn = db(json_path)
create_legacy_history(conn)
conn.execute(
    "INSERT INTO mind_canvas_history "
    "(id, canvas_id, action_type, snapshot_json, request_key, created_at) "
    "VALUES ('bad-json', 'c1', 'move', 'not-json', NULL, "
    "'2026-01-01T00:00:00Z')"
)
conn.commit()
conn.close()
run_in(json_env, "stamp", PREV_MERGE)
before = schema_snapshot(json_path)
run_in_expect_failure(
    json_env,
    "upgrade",
    "head",
    contains="JSON válido",
)
assert schema_snapshot(json_path) == before, "El aborto de JSON modificó el esquema"
check_version(PREV_MERGE, json_path)
print("OK aborto: snapshot inválido no modifica el esquema")

# 14. Aborto de historial con Canvas huérfano.
orphan_env, _, orphan_path = prepare_repair_db("lifeos_mig_hist_orphan_")
conn = db(orphan_path)
create_legacy_history(conn)
conn.execute("PRAGMA foreign_keys = OFF")
conn.execute(
    "INSERT INTO mind_canvas_history "
    "(id, canvas_id, action_type, snapshot_json, request_key, created_at) "
    "VALUES ('orphan', 'missing-canvas', 'move', '{}', NULL, "
    "'2026-01-01T00:00:00Z')"
)
conn.commit()
conn.close()
run_in(orphan_env, "stamp", PREV_MERGE)
before = schema_snapshot(orphan_path)
run_in_expect_failure(
    orphan_env,
    "upgrade",
    "head",
    contains="sin Canvas",
)
assert schema_snapshot(orphan_path) == before, "El aborto de huérfano modificó el esquema"
check_version(PREV_MERGE, orphan_path)
print("OK aborto: historial huérfano no modifica el esquema")

# 15. Aborto de historial con estado o secuencia inválidos.
state_env, _, state_path = prepare_repair_db("lifeos_mig_hist_state_")
conn = db(state_path)
create_partial_history(conn)
conn.executemany(
    "INSERT INTO mind_canvas_history "
    "(id, canvas_id, sequence, action_type, snapshot_json, state, created_at) "
    "VALUES (?, 'c1', ?, 'move', '{}', ?, '2026-01-01T00:00:00Z')",
    [
        ("bad-state", 1, "bogus"),
        ("dup-seq-1", 2, "applied"),
        ("dup-seq-2", 2, "applied"),
        ("bad-seq", 0, "applied"),
    ],
)
conn.commit()
conn.close()
run_in(state_env, "stamp", PREV_MERGE)
before = schema_snapshot(state_path)
run_in_expect_failure(
    state_env,
    "upgrade",
    "head",
    contains="state inválido",
)
assert schema_snapshot(state_path) == before, "El aborto de estado modificó el esquema"
check_version(PREV_MERGE, state_path)
print("OK aborto: estado/secuencia inválidos no modifican el esquema")

# 15b. Historial con columnas extra: aborta si contienen datos.
extra_env, _, extra_path = prepare_repair_db("lifeos_mig_hist_extra_")
conn = db(extra_path)
create_legacy_history(conn)
conn.execute("ALTER TABLE mind_canvas_history ADD COLUMN legacy_note TEXT")
conn.execute(
    "INSERT INTO mind_canvas_history "
    "(id, canvas_id, action_type, snapshot_json, request_key, created_at, "
    "legacy_note) VALUES ('extra-1', 'c1', 'move', '{}', 'extra-request', "
    "'2026-01-01T00:00:00Z', 'no descartar')"
)
conn.commit()
conn.close()
run_in(extra_env, "stamp", PREV_MERGE)
before = schema_snapshot(extra_path)
run_in_expect_failure(
    extra_env,
    "upgrade",
    "head",
    contains="columnas extra con datos",
)
assert schema_snapshot(extra_path) == before, (
    "El aborto de columnas extra modificó el esquema"
)
check_version(PREV_MERGE, extra_path)
print("OK aborto: columnas extra de history con datos no se descartan")

# 15c. Historial con columnas extra vacías: reconstruye y preserva filas.
extra_empty_env, _, extra_empty_path = prepare_repair_db(
    "lifeos_mig_hist_extra_empty_"
)
conn = db(extra_empty_path)
create_legacy_history(conn)
conn.execute("ALTER TABLE mind_canvas_history ADD COLUMN legacy_note TEXT")
conn.execute(
    "INSERT INTO mind_canvas_history "
    "(id, canvas_id, action_type, snapshot_json, request_key, created_at, "
    "legacy_note) VALUES ('extra-empty', 'c1', 'move', '{}', 'extra-empty', "
    "'2026-01-01T00:00:00Z', NULL)"
)
conn.commit()
conn.close()
run_repair(extra_empty_env, extra_empty_path)
history = table_rows(
    extra_empty_path,
    "SELECT id, sequence, state, request_key FROM mind_canvas_history "
    "WHERE id='extra-empty'",
)
assert history == [("extra-empty", 1, "applied", "extra-empty")], (
    f"Historial con columna extra vacía no preservado: {history}"
)
assert_final_mind_schema("columnas extra vacías de history", extra_empty_path)
print("OK columnas extra vacías de history: rebuild sin pérdida")


# 16. Edges legacy vacíos: se reconstruyen sin datos que perder.
empty_env, _, empty_path = prepare_repair_db("lifeos_mig_edge_empty_")
conn = db(empty_path)
create_legacy_edges(conn, metadata=True)
conn.commit()
conn.close()
run_repair(empty_env, empty_path)
assert table_columns("mind_canvas_edges", empty_path) == {
    "id",
    "canvas_id",
    "source_node_id",
    "target_node_id",
    "source_anchor",
    "target_anchor",
    "created_at",
    "updated_at",
}, "Edges legacy vacíos no convergieron al esquema final"
assert table_rows(empty_path, "SELECT COUNT(*) FROM mind_canvas_edges") == [(0,)]
assert_final_mind_schema("edges legacy vacíos", empty_path)
print("OK edges legacy vacíos: esquema final sin pérdida")

# 17. Aborto de edges legacy con metadatos y filas.
meta_env, _, meta_path = prepare_repair_db("lifeos_mig_edge_meta_")
conn = db(meta_path)
create_legacy_edges(conn, metadata=True)
conn.execute(
    "INSERT INTO mind_canvas_edges "
    "(id, canvas_id, source_node_id, target_node_id, source_anchor, "
    "target_anchor, created_at, updated_at, edge_type, style_json, "
    "ai_suggested, ai_confidence) VALUES "
    "('legacy-edge', 'c1', 'm1', 'm2', '0', '0', "
    "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z', 'related', "
    "'{\"color\": \"red\"}', 1, 0.9)"
)
conn.commit()
conn.close()
run_in(meta_env, "stamp", PREV_MERGE)
before = schema_snapshot(meta_path)
run_in_expect_failure(
    meta_env,
    "upgrade",
    "head",
    contains="metadatos legacy",
)
assert schema_snapshot(meta_path) == before, "El aborto de metadatos modificó el esquema"
check_version(PREV_MERGE, meta_path)
print("OK aborto: metadatos legacy de edges no se descartan")

# 18. Edges representables con filas: se normalizan y preservan.
repr_env, _, repr_path = prepare_repair_db("lifeos_mig_edge_repr_")
conn = db(repr_path)
create_partial_edges(conn)
conn.execute(
    "INSERT INTO mind_canvas_edges "
    "(id, canvas_id, source_node_id, target_node_id, source_anchor, "
    "target_anchor, created_at, updated_at) VALUES "
    "('e1', 'c1', 'm2', 'm1', '3', '4', "
    "'2026-01-01T00:00:00Z', '2026-01-02T00:00:00Z')"
)
conn.commit()
conn.close()
run_repair(repr_env, repr_path)
edge = table_rows(
    repr_path,
    "SELECT id, source_node_id, target_node_id, source_anchor, target_anchor, "
    "created_at, updated_at FROM mind_canvas_edges WHERE id='e1'",
)
assert edge == [
    (
        "e1",
        "m1",
        "m2",
        4,
        3,
        "2026-01-01T00:00:00Z",
        "2026-01-02T00:00:00Z",
    )
], f"Edge legacy no preservada: {edge}"
assert_final_mind_schema("edges representables preservados", repr_path)
print("OK edges representables: extremos, anclajes y timestamps preservados")

# 19. Aborto de edges con self-loop, cruce de Canvas, anclaje o duplicado.
bad_env, _, bad_path = prepare_repair_db("lifeos_mig_edge_bad_")
conn = db(bad_path)
create_partial_edges(conn)
conn.executemany(
    "INSERT INTO mind_canvas_edges "
    "(id, canvas_id, source_node_id, target_node_id, source_anchor, "
    "target_anchor, created_at, updated_at) VALUES "
    "(?, 'c1', ?, ?, ?, ?, '2026-01-01T00:00:00Z', "
    "'2026-01-01T00:00:00Z')",
    [
        ("bad-self", "m1", "m1", "0", "0"),
        ("bad-cross", "m1", "m3", "0", "0"),
        ("bad-anchor", "m1", "m2", "invalid", "0"),
        ("dup-1", "m1", "m2", "0", "0"),
        ("dup-2", "m2", "m1", "0", "0"),
    ],
)
conn.commit()
conn.close()
run_in(bad_env, "stamp", PREV_MERGE)
before = schema_snapshot(bad_path)
run_in_expect_failure(
    bad_env,
    "upgrade",
    "head",
    contains="datos incompatibles",
)
assert schema_snapshot(bad_path) == before, "El aborto de edges modificó el esquema"
check_version(PREV_MERGE, bad_path)
print("OK aborto: edges inválidas no modifican el esquema")

# 20. Índice único de nodos ausente: se crea sin tocar los nodos.
node_env, _, node_path = prepare_repair_db("lifeos_mig_node_idx_")
conn = db(node_path)
conn.execute("DROP INDEX uq_mind_canvas_nodes_canvas_id_id")
conn.commit()
conn.close()
run_repair(node_env, node_path)
node_indexes = table_rows(
    node_path, "PRAGMA index_list(mind_canvas_nodes)"
)
assert any(row[1] == "uq_mind_canvas_nodes_canvas_id_id" and row[2] == 1 for row in node_indexes)
assert table_rows(node_path, "SELECT COUNT(*) FROM mind_canvas_nodes") == [(3,)]
assert_final_mind_schema("índice de nodos creado", node_path)
print("OK índice único de nodos creado sin alterar filas")

# 21. Índice de nodos incorrecto: aborta con diagnóstico.
wrong_env, _, wrong_path = prepare_repair_db("lifeos_mig_node_bad_")
conn = db(wrong_path)
conn.execute("DROP INDEX uq_mind_canvas_nodes_canvas_id_id")
conn.execute(
    "CREATE INDEX uq_mind_canvas_nodes_canvas_id_id "
    "ON mind_canvas_nodes (canvas_id, id)"
)
conn.commit()
conn.close()
run_in(wrong_env, "stamp", PREV_MERGE)
before = schema_snapshot(wrong_path)
run_in_expect_failure(
    wrong_env,
    "upgrade",
    "head",
    contains="no es único",
)
assert schema_snapshot(wrong_path) == before, "El aborto de índice modificó el esquema"
check_version(PREV_MERGE, wrong_path)
print("OK aborto: índice de nodos incorrecto no modifica el esquema")

# 22. Índices de history/edges ausentes: solo se recrean.
index_env, _, index_path = prepare_repair_db("lifeos_mig_index_")
conn = db(index_path)
conn.execute(
    "INSERT INTO mind_canvas_history "
    "(id, canvas_id, sequence, action_type, snapshot_json, request_key, "
    "state, created_at) VALUES "
    "('h1', 'c1', 1, 'move', '{}', 'r1', 'applied', "
    "'2026-01-01T00:00:00Z')"
)
conn.execute(
    "INSERT INTO mind_canvas_edges "
    "(id, canvas_id, source_node_id, target_node_id, source_anchor, "
    "target_anchor, created_at, updated_at) VALUES "
    "('e1', 'c1', 'm1', 'm2', 0, 0, "
    "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
)
conn.execute("DROP INDEX ix_mind_canvas_history_canvas_created")
conn.execute("DROP INDEX ix_mind_canvas_edges_canvas_target")
conn.commit()
conn.close()
run_repair(index_env, index_path)
assert table_rows(index_path, "SELECT COUNT(*) FROM mind_canvas_history") == [(1,)]
assert table_rows(index_path, "SELECT COUNT(*) FROM mind_canvas_edges") == [(1,)]
assert_final_mind_schema("índices recreados", index_path)
print("OK índices ausentes recreados sin alterar filas")

# 23. Re-ejecutar 0010 sobre el esquema final es un no-op.
before_snapshot = schema_snapshot(DB_PATH)
before_signature = mind_schema_signature(DB_PATH)
run("stamp", PREV_MERGE)
run("upgrade", "head")
assert schema_snapshot(DB_PATH) == before_snapshot, "0010 no fue idempotente"
assert mind_schema_signature(DB_PATH) == before_signature
check_version(HEAD)
run("check")
print("OK 0010 idempotente: sin DDL ni cambios de esquema")

# 24. Base híbrida real: multi-stamp evita 0006_home y llega a 0010.
hybrid_env, _, hybrid_path = make_env("lifeos_mig_hybrid_")
run_in(hybrid_env, "upgrade", PREV_MIND)
conn = db(hybrid_path)
conn.execute(
    "ALTER TABLE widget_preferences ADD COLUMN column_span INTEGER NOT NULL "
    "DEFAULT 2"
)
conn.execute(
    "ALTER TABLE widget_preferences ADD COLUMN row_span INTEGER NOT NULL "
    "DEFAULT 1"
)
conn.execute(
    "INSERT INTO widget_preferences "
    "(widget_id, is_visible, position, config_json, updated_at, column_span, "
    "row_span) VALUES ('upcoming_tasks', 1, 7, NULL, "
    "'2026-01-01T00:00:00Z', 4, 2)"
)
seed_mind_graph(conn)
create_legacy_edges(conn, metadata=True)
create_legacy_history(conn)
conn.commit()
conn.close()
run_in(hybrid_env, "stamp", "0008_mind_canvas_history")
before = schema_snapshot(hybrid_path)
run_in_expect_failure(
    hybrid_env,
    "upgrade",
    "head",
    contains="column_span",
)
assert schema_snapshot(hybrid_path) == before, (
    "El intento sin multi-stamp modificó el esquema híbrido"
)
check_version("0008_mind_canvas_history", hybrid_path)
run_in(
    hybrid_env,
    "stamp",
    "0006_home_widget_grid",
    "0008_mind_canvas_history",
)
result = run_in(hybrid_env, "upgrade", "head")
combined = result.stdout + "\n" + result.stderr
assert "-> 0009_merge_evolution_mind" in combined, combined
assert "-> 0010_repair_mind_canvas_schema" in combined, combined
for skipped in (
    "-> 0006_home_widget_grid",
    "-> 0007_mind_canvas_edges",
    "-> 0008_mind_canvas_history",
):
    assert skipped not in combined, (
        f"Se re-ejecutó una migración antigua: {skipped}\n{combined}"
    )
check_version(HEAD, hybrid_path)
spans = table_rows(
    hybrid_path,
    "SELECT position, column_span, row_span FROM widget_preferences "
    "WHERE widget_id='upcoming_tasks'",
)
assert spans == [(7, 4, 2)], f"El layout del usuario cambió: {spans}"
assert_final_mind_schema("base híbrida multi-stamp", hybrid_path)
check_integrity("base híbrida multi-stamp", hybrid_path)
run_in(hybrid_env, "check")
print("OK base híbrida: multi-stamp -> 0009 -> 0010 sin re-ejecutar 0006-0008")

# 25. Backup WAL: incluye frames confirmados y verifica integridad.
backup_dir = tempfile.mkdtemp(prefix="lifeos_backup_")
wal_source = os.path.join(backup_dir, "source.db")
wal_backup = os.path.join(backup_dir, "backup.db")
writer = sqlite3.connect(wal_source)
try:
    writer.execute("PRAGMA journal_mode = WAL")
    writer.execute("PRAGMA wal_autocheckpoint = 0")
    writer.execute("CREATE TABLE items (id INTEGER PRIMARY KEY, value TEXT)")
    writer.execute("INSERT INTO items (value) VALUES ('en-wal')")
    writer.commit()
    assert os.path.exists(wal_source + "-wal"), "No se creó el archivo WAL"
    backup_result = subprocess.run(
        [
            sys.executable,
            "backup_db.py",
            "--source",
            wal_source,
            "--destination",
            wal_backup,
        ],
        env=os.environ,
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=os.path.dirname(__file__),
    )
    print(backup_result.stdout.strip())
    print(backup_result.stderr.strip())
    assert backup_result.returncode == 0, backup_result.stderr
    assert '"integrity_check": "ok"' in backup_result.stdout
    backup_conn = sqlite3.connect(wal_backup)
    try:
        assert backup_conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert backup_conn.execute("SELECT value FROM items").fetchall() == [
            ("en-wal",)
        ]
    finally:
        backup_conn.close()
finally:
    writer.close()
print("OK backup WAL: datos confirmados incluidos e integridad verificada")

print(f"\nTODAS LAS VERIFICACIONES PASARON (dir: {DATA_DIR})")
