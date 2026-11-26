"""Pruebas de exportación JSON (Fase 5)."""

import json

from sqlalchemy import delete, select

from app.modules.mind.models import MindCanvasHistory


def test_export_returns_versioned_json(client):
    """La exportación debe devolver JSON con format_version y todas las tablas."""
    client.post("/api/v1/projects", json={"name": "Proyecto 1", "status": "active"})
    client.post("/api/v1/tasks", json={"title": "Tarea 1", "status": "pending"})
    habit = client.post(
        "/api/v1/habits",
        json={"name": "Diario", "start_date": "2026-01-01", "frequency_type": "daily"},
    ).json()
    client.post(
        f"/api/v1/habits/{habit['id']}/entries",
        json={"entry_date": "2026-01-02"},
    )

    response = client.get("/api/v1/export")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["x-lifeos-format-version"] == "2"

    data = response.json()
    assert data["format_version"] == 2
    assert "exported_at" in data
    assert len(data["projects"]) == 1
    assert len(data["tasks"]) == 1
    assert data["projects"][0]["name"] == "Proyecto 1"
    assert data["tasks"][0]["title"] == "Tarea 1"
    # Hábitos y sus registros incluidos (Fase 7) con IDs y relaciones
    assert len(data["habits"]) == 1
    assert data["habits"][0]["name"] == "Diario"
    assert len(data["habit_entries"]) == 1
    assert data["habit_entries"][0]["habit_id"] == habit["id"]
    assert data["habit_entries"][0]["entry_date"] == "2026-01-02"
    # Todas las tablas del MVP presentes
    for key in [
        "notes",
        "note_project_links",
        "note_task_links",
        "tags",
        "note_tags",
        "habits",
        "habit_entries",
        "mind_spaces",
        "mind_canvases",
        "mind_space_notes",
        "mind_canvas_nodes",
        "mind_canvas_edges",
        "mind_canvas_history",
        "widget_preferences",
        "user_preferences",
        "activity_events",
    ]:
        assert key in data
        assert isinstance(data[key], list)

    response = client.put(
        "/api/v1/dashboard/widgets",
        json=[
            {
                "widget_id": "upcoming_tasks",
                "position": 1,
                "column_span": 5,
                "row_span": 2,
            }
        ],
    )
    assert response.status_code == 200
    exported_preferences = client.get("/api/v1/export").json()["widget_preferences"]
    tasks_preference = next(
        preference
        for preference in exported_preferences
        if preference["widget_id"] == "upcoming_tasks"
    )
    assert tasks_preference["column_span"] == 5
    assert tasks_preference["row_span"] == 2


def test_import_rejects_invalid_json_and_unknown_fields(client):
    invalid = client.post("/api/v1/import", json={"payload": "{"})
    assert invalid.status_code == 422, invalid.text

    unknown = client.post(
        "/api/v1/import",
        json={
            "payload": '{"format_version": 2, "unknown_table": []}',
        },
    )
    assert unknown.status_code == 422, unknown.text

    invalid_history = client.post(
        "/api/v1/import",
        json={
            "payload": json.dumps(
                {
                    "format_version": 2,
                    "mind_canvas_history": [
                        {
                            "id": "invalid-history",
                            "canvas_id": "missing-canvas",
                            "sequence": 1,
                            "action_type": "move",
                            "snapshot_json": "{}",
                            "inverse_json": None,
                            "request_key": None,
                            "state": "invalid",
                            "undone_at": None,
                            "created_at": "2026-01-01T00:00:00Z",
                        }
                    ],
                }
            )
        },
    )
    assert invalid_history.status_code == 422, invalid_history.text


def test_import_is_idempotent_and_preserves_fk_order(client):
    project = client.post(
        "/api/v1/projects", json={"name": "Proyecto importable"}
    ).json()
    task = client.post(
        "/api/v1/tasks",
        json={"title": "Tarea importable", "project_id": project["id"]},
    ).json()
    note = client.post(
        "/api/v1/notes", json={"title": "Nota importable", "content": "Contenido"}
    ).json()
    link = client.post(
        f"/api/v1/notes/{note['id']}/tasks",
        json={"id": task["id"]},
    )
    assert link.status_code == 204, link.text

    exported = client.get("/api/v1/export").json()
    response = client.post(
        "/api/v1/import",
        json={"payload": json.dumps(exported)},
    )
    assert response.status_code == 200, response.text
    assert response.json()["inserted"] == 0
    assert response.json()["skipped"] > 0


def test_export_import_preserves_canvas_history(client, db):
    space = client.post(
        "/api/v1/mind/spaces",
        json={"name": "Space exportable"},
    ).json()
    canvas = client.post(
        f"/api/v1/mind/spaces/{space['id']}/canvases",
        json={"title": "Canvas exportable"},
    ).json()
    card = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/cards",
        json={"content": "Card exportable"},
    ).json()
    moved = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "move",
            "nodes": [{"id": card["id"], "x": 42.0, "y": 84.0}],
        },
        headers={"Idempotency-Key": "export-history-move"},
    )
    assert moved.status_code == 200, moved.text

    exported = client.get("/api/v1/export").json()
    rows = [
        row
        for row in exported["mind_canvas_history"]
        if row["canvas_id"] == canvas["id"]
    ]
    assert len(rows) >= 2
    original = max(rows, key=lambda row: row["sequence"])

    db.execute(
        delete(MindCanvasHistory).where(MindCanvasHistory.id == original["id"])
    )
    db.flush()

    response = client.post(
        "/api/v1/import",
        json={"payload": json.dumps(exported)},
    )
    assert response.status_code == 200, response.text
    assert response.json()["inserted"] == 1

    restored = db.get(MindCanvasHistory, original["id"])
    assert restored is not None
    for field in (
        "canvas_id",
        "sequence",
        "action_type",
        "snapshot_json",
        "inverse_json",
        "request_key",
        "state",
        "undone_at",
        "created_at",
    ):
        assert getattr(restored, field) == original[field]


def test_import_integrity_error_does_not_leave_partial_data(client):
    payload = {
        "format_version": 2,
        "projects": [],
        "tasks": [
            {
                "id": "task-with-missing-project",
                "project_id": "missing-project",
                "title": "Tarea inválida",
                "description": None,
                "status": "pending",
                "priority": None,
                "due_date": None,
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "completed_at": None,
            }
        ],
    }
    response = client.post(
        "/api/v1/import",
        json={"payload": json.dumps(payload)},
    )
    assert response.status_code == 409, response.text
    assert client.get("/api/v1/tasks").json() == []
