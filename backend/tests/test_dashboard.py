"""Pruebas de API e integración para Dashboard y configuración."""




def test_list_widgets_defaults(client):
    """El catálogo debe devolver los widgets del MVP (Fase 6 + 7) con defaults."""
    response = client.get("/api/v1/dashboard/widgets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 6
    ids = [w["widget_id"] for w in data]
    assert "upcoming_tasks" in ids
    assert "active_projects" in ids
    assert "quick_add_task" in ids
    assert "quick_add_note" in ids
    assert "habits_today" in ids
    assert "habits_week" in ids
    # Todos visibles por defecto
    assert all(w["is_visible"] is True for w in data)
    # Orden por posición
    positions = [w["position"] for w in data]
    assert positions == sorted(positions)
    by_id = {widget["widget_id"]: widget for widget in data}
    assert by_id["upcoming_tasks"]["column_span"] == 4
    assert by_id["upcoming_tasks"]["row_span"] == 1
    assert by_id["quick_add_task"]["position"] == by_id["quick_add_note"]["position"]
    assert by_id["habits_week"]["row_span"] == 1


def test_save_widget_preferences(client):
    """Se pueden guardar preferencias de visibilidad y orden de widgets."""
    prefs = [
        {"widget_id": "upcoming_tasks", "is_visible": True, "position": 0},
        {"widget_id": "active_projects", "is_visible": False, "position": 1},
        {"widget_id": "quick_add_task", "is_visible": True, "position": 2},
        {"widget_id": "quick_add_note", "is_visible": False, "position": 3},
    ]
    response = client.put("/api/v1/dashboard/widgets", json=prefs)
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data) == 4

    # Verificar que se persisten
    response = client.get("/api/v1/dashboard/widgets")
    assert response.status_code == 200
    data = response.json()
    by_id = {w["widget_id"]: w for w in data}
    assert by_id["active_projects"]["is_visible"] is False
    assert by_id["quick_add_note"]["is_visible"] is False
    assert not by_id["active_projects"]["is_visible"]
    assert not by_id["quick_add_note"]["is_visible"]
    assert by_id["active_projects"]["column_span"] == 4
    assert by_id["quick_add_task"]["position"] == by_id["quick_add_note"]["position"]
    assert by_id["quick_add_note"]["row_span"] == 1


def test_widget_layout_round_trip(client):
    """Se conservan orden y spans dentro del catálogo de widgets."""
    prefs = [
        {
            "widget_id": "upcoming_tasks",
            "is_visible": True,
            "position": 2,
            "column_span": 6,
            "row_span": 3,
        },
        {
            "widget_id": "quick_add_task",
            "is_visible": True,
            "position": 0,
            "column_span": 2,
            "row_span": 1,
        },
        {
            "widget_id": "quick_add_note",
            "is_visible": False,
            "position": 0,
            "column_span": 2,
            "row_span": 1,
        },
    ]
    response = client.put("/api/v1/dashboard/widgets", json=prefs)
    assert response.status_code == 200, response.text

    data = client.get("/api/v1/dashboard/widgets").json()
    by_id = {widget["widget_id"]: widget for widget in data}
    assert by_id["upcoming_tasks"]["position"] == 2
    assert by_id["upcoming_tasks"]["column_span"] == 6
    assert by_id["upcoming_tasks"]["row_span"] == 3
    assert by_id["quick_add_task"]["position"] == by_id["quick_add_note"]["position"] == 0

    legacy_update = client.put(
        "/api/v1/dashboard/widgets",
        json=[
            {"widget_id": "upcoming_tasks", "is_visible": False, "position": 1}
        ],
    )
    assert legacy_update.status_code == 200
    persisted = {
        widget["widget_id"]: widget
        for widget in client.get("/api/v1/dashboard/widgets").json()
    }
    assert persisted["upcoming_tasks"]["column_span"] == 6
    assert persisted["upcoming_tasks"]["row_span"] == 3

    capture_update = client.put(
        "/api/v1/dashboard/widgets",
        json=[
            {
                "widget_id": "quick_add_note",
                "position": 3,
                "column_span": 3,
                "row_span": 2,
            }
        ],
    )
    assert capture_update.status_code == 200
    persisted = {
        widget["widget_id"]: widget
        for widget in client.get("/api/v1/dashboard/widgets").json()
    }
    assert persisted["quick_add_task"]["position"] == 3
    assert persisted["quick_add_task"]["column_span"] == 3
    assert persisted["quick_add_task"]["row_span"] == 2
    assert persisted["quick_add_note"]["position"] == 3
    assert persisted["quick_add_note"]["column_span"] == 3
    assert persisted["quick_add_note"]["row_span"] == 2


def test_invalid_widget_span_does_not_write_any_preferences(client):
    """Un span fuera de rango rechaza el lote antes de persistir cambios."""
    before = client.get("/api/v1/dashboard/widgets").json()
    response = client.put(
        "/api/v1/dashboard/widgets",
        json=[
            {"widget_id": "upcoming_tasks", "position": 5},
            {"widget_id": "active_projects", "column_span": 7},
        ],
    )
    assert response.status_code == 422
    after = client.get("/api/v1/dashboard/widgets").json()
    assert after == before


def test_duplicate_or_unknown_widget_rejects_batch(client):
    """IDs duplicados o ajenos al catálogo no escriben preferencias parciales."""
    before = client.get("/api/v1/dashboard/widgets").json()
    for preferences in (
        [
            {"widget_id": "upcoming_tasks", "position": 3},
            {"widget_id": "upcoming_tasks", "position": 4},
        ],
        [{"widget_id": "unknown_widget", "position": 1}],
    ):
        response = client.put("/api/v1/dashboard/widgets", json=preferences)
        assert response.status_code == 422
        assert client.get("/api/v1/dashboard/widgets").json() == before

    mismatched_capture = client.put(
        "/api/v1/dashboard/widgets",
        json=[
            {
                "widget_id": "quick_add_task",
                "position": 1,
                "column_span": 2,
                "row_span": 1,
            },
            {
                "widget_id": "quick_add_note",
                "position": 1,
                "column_span": 3,
                "row_span": 1,
            },
        ],
    )
    assert mismatched_capture.status_code == 422
    assert client.get("/api/v1/dashboard/widgets").json() == before


def test_dashboard_summary(client):
    """El resumen del dashboard debe devolver métricas básicas."""
    # Crear algunos proyectos y tareas para tener datos
    client.post("/api/v1/projects", json={"name": "Proyecto 1", "status": "active"})
    client.post("/api/v1/projects", json={"name": "Proyecto 2", "status": "archived"})
    client.post("/api/v1/tasks", json={"title": "Tarea pendiente 1", "status": "pending"})
    client.post(
        "/api/v1/tasks", json={"title": "Tarea pendiente 2", "status": "pending"}
    )
    client.post("/api/v1/tasks", json={"title": "Tarea completada", "status": "completed"})

    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["tasks"]["pending"] == 2
    assert data["tasks"]["completed"] == 1
    assert data["projects"]["active"] == 1


def test_dashboard_summary_empty(client):
    """Resumen del dashboard con base vacía."""
    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["tasks"]["pending"] == 0
    assert data["tasks"]["completed"] == 0
    assert data["projects"]["active"] == 0