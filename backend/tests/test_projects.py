"""Pruebas de API e integración para Proyectos."""

from datetime import date, datetime, timedelta

from fastapi.testclient import TestClient


def _client(client: TestClient) -> TestClient:
    return client


def test_create_project(client):
    response = client.post(
        "/api/v1/projects",
        json={"name": "Proyecto A", "description": "Descripción de prueba"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Proyecto A"
    assert data["description"] == "Descripción de prueba"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_project_duplicate_allowed(client):
    """Se pueden crear varios proyectos con el mismo nombre (no hay restricción de unicidad)."""
    client.post("/api/v1/projects", json={"name": "Proyecto X"})
    response = client.post("/api/v1/projects", json={"name": "Proyecto X"})
    assert response.status_code == 201


def test_create_project_empty_name_rejected(client):
    response = client.post("/api/v1/projects", json={"name": "   "})
    assert response.status_code == 422


def test_create_project_invalid_status_rejected(client):
    response = client.post(
        "/api/v1/projects", json={"name": "Proyecto", "status": "invalido"}
    )
    assert response.status_code == 422


def test_list_projects(client):
    client.post("/api/v1/projects", json={"name": "Proyecto 1", "status": "active"})
    client.post("/api/v1/projects", json={"name": "Proyecto 2", "status": "archived"})
    response = client.get("/api/v1/projects")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_projects_filter_by_status(client):
    client.post("/api/v1/projects", json={"name": "Activo", "status": "active"})
    client.post("/api/v1/projects", json={"name": "Archivado", "status": "archived"})
    response = client.get("/api/v1/projects?status=active")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Activo"


def test_get_project(client):
    create = client.post(
        "/api/v1/projects", json={"name": "Proyecto Uno"}
    )
    project_id = create.json()["id"]
    response = client.get(f"/api/v1/projects/{project_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == project_id
    assert data["name"] == "Proyecto Uno"


def test_get_project_not_found(client):
    response = client.get("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_project(client):
    create = client.post("/api/v1/projects", json={"name": "Original"})
    project_id = create.json()["id"]
    response = client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Modificado", "status": "completed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Modificado"
    assert data["status"] == "completed"


def test_complete_project(client):
    create = client.post("/api/v1/projects", json={"name": "Para completar"})
    project_id = create.json()["id"]
    response = client.post(f"/api/v1/projects/{project_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["completed_at"] is not None


def test_reopen_project(client):
    create = client.post("/api/v1/projects", json={"name": "Para reabrir"})
    project_id = create.json()["id"]
    client.post(f"/api/v1/projects/{project_id}/complete")
    response = client.post(f"/api/v1/projects/{project_id}/reopen")
    assert response.status_code == 200
    assert response.json()["status"] == "active"
    assert response.json()["completed_at"] is None


def test_archive_project(client):
    create = client.post("/api/v1/projects", json={"name": "Para archivar"})
    project_id = create.json()["id"]
    response = client.post(f"/api/v1/projects/{project_id}/archive")
    assert response.status_code == 200
    assert response.json()["status"] == "archived"
    assert response.json()["archived_at"] is not None


def test_restore_project(client):
    create = client.post("/api/v1/projects", json={"name": "Para restaurar"})
    project_id = create.json()["id"]
    client.post(f"/api/v1/projects/{project_id}/archive")
    response = client.post(f"/api/v1/projects/{project_id}/restore")
    assert response.status_code == 200
    assert response.json()["status"] == "active"
    assert response.json()["archived_at"] is None


def test_delete_project_without_tasks(client):
    create = client.post("/api/v1/projects", json={"name": "Para eliminar"})
    project_id = create.json()["id"]
    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 204


def test_delete_project_with_tasks_rejected(client):
    """No se puede eliminar físicamente un proyecto que tiene tareas (ON DELETE RESTRICT)."""
    proj = client.post("/api/v1/projects", json={"name": "Con tarea"})
    project_id = proj.json()["id"]
    client.post(
        "/api/v1/tasks",
        json={"title": "Tarea vinculada", "project_id": project_id},
    )
    response = client.delete(f"/api/v1/projects/{project_id}")
    assert response.status_code == 409


def test_delete_project_not_found(client):
    response = client.delete("/api/v1/projects/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


# --- Métricas de seguimiento (Rediseño Etapa 1) ------------------------------


def _local_today() -> date:
    """Fecha local efectiva del backend (misma zona que app.core.clock)."""
    from zoneinfo import ZoneInfo

    from app.core.clock import DEFAULT_TIMEZONE

    return datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).date()


def _create_project_with_tasks(client, tasks: list[dict]) -> str:
    proj = client.post("/api/v1/projects", json={"name": "Proyecto métricas"})
    project_id = proj.json()["id"]
    for payload in tasks:
        response = client.post(
            "/api/v1/tasks",
            json={"project_id": project_id, **payload},
        )
        assert response.status_code == 201, response.text
    return project_id


def test_project_metrics_zero_tasks(client):
    """Proyecto sin tareas: task_count=0 y next_due_date=None (frontend muestra 'Sin tareas')."""
    proj = client.post("/api/v1/projects", json={"name": "Vacío"})
    project_id = proj.json()["id"]
    data = client.get(f"/api/v1/projects/{project_id}").json()
    assert data["task_count"] == 0
    assert data["completed_count"] == 0
    assert data["overdue_count"] == 0
    assert data["next_due_date"] is None


def test_project_metrics_counts_and_avance_base(client):
    """Avance = completadas/total; las métricas vienen en listado y detalle."""
    today = _local_today()
    project_id = _create_project_with_tasks(
        client,
        [
            {"title": "Hecha 1", "status": "completed"},
            {"title": "Hecha 2", "status": "completed"},
            {"title": "Pendiente futura", "due_date": (today + timedelta(days=3)).isoformat()},
        ],
    )
    detail = client.get(f"/api/v1/projects/{project_id}").json()
    assert detail["task_count"] == 3
    assert detail["completed_count"] == 2
    assert detail["overdue_count"] == 0
    assert detail["next_due_date"] == (today + timedelta(days=3)).isoformat()

    listed = client.get("/api/v1/projects").json()
    match = next(p for p in listed if p["id"] == project_id)
    assert match["task_count"] == 3
    assert match["completed_count"] == 2


def test_project_metrics_overdue_and_next_due(client):
    """Vencidas = pending con due_date < hoy; próximo vencimiento = menor due >= hoy entre pending."""
    today = _local_today()
    project_id = _create_project_with_tasks(
        client,
        [
            {"title": "Vieja 1", "due_date": (today - timedelta(days=5)).isoformat()},
            {"title": "Vieja 2", "due_date": (today - timedelta(days=1)).isoformat()},
            {"title": "Futura lejana", "due_date": (today + timedelta(days=10)).isoformat()},
            {"title": "Futura próxima", "due_date": (today + timedelta(days=2)).isoformat()},
            {"title": "Sin fecha"},
        ],
    )
    data = client.get(f"/api/v1/projects/{project_id}").json()
    assert data["task_count"] == 5
    assert data["overdue_count"] == 2
    assert data["next_due_date"] == (today + timedelta(days=2)).isoformat()


def test_project_metrics_completed_past_due_not_overdue(client):
    """Una tarea completada con vencimiento pasado no cuenta como vencida."""
    today = _local_today()
    project_id = _create_project_with_tasks(
        client,
        [
            {
                "title": "Terminada tarde",
                "status": "completed",
                "due_date": (today - timedelta(days=2)).isoformat(),
            }
        ],
    )
    data = client.get(f"/api/v1/projects/{project_id}").json()
    assert data["completed_count"] == 1
    assert data["overdue_count"] == 0
    assert data["next_due_date"] is None


def test_project_metrics_due_today_is_next_due_not_overdue(client):
    """Una tarea con due_date = hoy no está vencida y sí puede ser el próximo vencimiento."""
    today = _local_today()
    project_id = _create_project_with_tasks(
        client, [{"title": "Para hoy", "due_date": today.isoformat()}]
    )
    data = client.get(f"/api/v1/projects/{project_id}").json()
    assert data["overdue_count"] == 0
    assert data["next_due_date"] == today.isoformat()