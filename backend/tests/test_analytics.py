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
    assert data["habits"]["active"] == 0
    assert data["habits"]["scheduled_today"] == 0
    assert data["habits"]["completed_today"] == 0


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


def test_analytics_summary_includes_habits(client):
    """Hábitos en el resumen: solo estados guardados del día local (Fase 7)."""
    from datetime import date

    today = date.today().isoformat()
    habit = client.post(
        "/api/v1/habits",
        json={"name": "Diario", "start_date": today, "frequency_type": "daily"},
    ).json()
    paused = client.post(
        "/api/v1/habits",
        json={"name": "Pausado", "start_date": today, "frequency_type": "daily"},
    ).json()
    client.post(f"/api/v1/habits/{paused['id']}/pause")
    # Registro completado de hoy
    client.post(f"/api/v1/habits/{habit['id']}/entries", json={})

    response = client.get("/api/v1/analytics/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["habits"]["active"] == 1  # el pausado no cuenta
    assert data["habits"]["scheduled_today"] == 1
    assert data["habits"]["completed_today"] == 1
    assert data["habits"]["skipped_today"] == 0
    assert data["habits"]["pending_today"] == 0
