"""Pruebas de exportación JSON (Fase 5)."""



def test_export_returns_versioned_json(client):
    """La exportación debe devolver JSON con format_version y todas las tablas."""
    client.post("/api/v1/projects", json={"name": "Proyecto 1", "status": "active"})
    client.post("/api/v1/tasks", json={"title": "Tarea 1", "status": "pending"})

    response = client.get("/api/v1/export")
    assert response.status_code == 200, response.text
    assert response.headers["content-type"].startswith("application/json")
    assert response.headers["x-lifeos-format-version"] == "1"

    data = response.json()
    assert data["format_version"] == 1
    assert "exported_at" in data
    assert len(data["projects"]) == 1
    assert len(data["tasks"]) == 1
    assert data["projects"][0]["name"] == "Proyecto 1"
    assert data["tasks"][0]["title"] == "Tarea 1"
    # Todas las tablas del MVP presentes
    for key in [
        "notes",
        "note_project_links",
        "note_task_links",
        "tags",
        "note_tags",
        "widget_preferences",
        "user_preferences",
        "activity_events",
    ]:
        assert key in data
        assert isinstance(data[key], list)
