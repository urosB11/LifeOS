"""Pruebas de API e integración para Dashboard y configuración."""




def test_list_widgets_defaults(client):
    """El catálogo de widgets debe devolver los 4 widgets del MVP con defaults."""
    response = client.get("/api/v1/dashboard/widgets")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 4
    ids = [w["widget_id"] for w in data]
    assert "upcoming_tasks" in ids
    assert "active_projects" in ids
    assert "quick_add_task" in ids
    assert "quick_add_note" in ids
    # Todos visibles por defecto
    assert all(w["is_visible"] is True for w in data)
    # Orden por posición
    positions = [w["position"] for w in data]
    assert positions == sorted(positions)


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