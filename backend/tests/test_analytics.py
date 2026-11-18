"""Pruebas de Analytics básico (Fase 5)."""



def test_analytics_summary_empty(client):
    """Resumen analítico con base vacía."""
    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["format_version"] == 1
    assert data["tasks"]["pending"] == 0
    assert data["tasks"]["completed"] == 0
    assert data["tasks"]["overdue"] == 0
    assert data["projects"]["active"] == 0


def test_analytics_summary_with_data(client):
    """Resumen analítico con tareas y proyectos creados."""
    client.post("/api/v1/projects", json={"name": "Activo", "status": "active"})
    client.post("/api/v1/projects", json={"name": "Archivado", "status": "archived"})
    client.post("/api/v1/tasks", json={"title": "Pendiente 1", "status": "pending"})
    client.post("/api/v1/tasks", json={"title": "Pendiente 2", "status": "pending"})
    client.post("/api/v1/tasks", json={"title": "Completada", "status": "completed"})

    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["tasks"]["pending"] == 2
    assert data["tasks"]["completed"] == 1
    assert data["projects"]["active"] == 1
