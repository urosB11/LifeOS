"""Pruebas de exportación JSON (Fase 5)."""



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
