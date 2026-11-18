"""Pruebas de API e integración para Tareas."""




def test_create_task(client):
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "Tarea de prueba",
            "description": "Descripción",
            "priority": "high",
            "due_date": "2026-12-01",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["title"] == "Tarea de prueba"
    assert data["priority"] == "high"
    assert data["due_date"] == "2026-12-01"
    assert data["status"] == "pending"
    assert "id" in data


def test_create_task_with_project(client):
    proj = client.post("/api/v1/projects", json={"name": "Proyecto padre"})
    project_id = proj.json()["id"]
    response = client.post(
        "/api/v1/tasks",
        json={"title": "Tarea con proyecto", "project_id": project_id},
    )
    assert response.status_code == 201
    assert response.json()["project_id"] == project_id


def test_create_task_with_nonexistent_project_rejected(client):
    response = client.post(
        "/api/v1/tasks",
        json={"title": "Tarea huérfana", "project_id": "00000000-0000-0000-0000-000000000000"},
    )
    assert response.status_code == 400


def test_create_task_empty_title_rejected(client):
    response = client.post("/api/v1/tasks", json={"title": "   "})
    assert response.status_code == 422


def test_create_task_invalid_priority_rejected(client):
    response = client.post(
        "/api/v1/tasks", json={"title": "Tarea", "priority": "urgente"}
    )
    assert response.status_code == 422


def test_create_task_invalid_due_date_rejected(client):
    response = client.post(
        "/api/v1/tasks", json={"title": "Tarea", "due_date": "01-12-2026"}
    )
    assert response.status_code == 422


def test_list_tasks(client):
    client.post("/api/v1/tasks", json={"title": "T1", "status": "pending"})
    client.post("/api/v1/tasks", json={"title": "T2", "status": "completed"})
    response = client.get("/api/v1/tasks")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_tasks_filter_by_status(client):
    client.post("/api/v1/tasks", json={"title": "Pendiente", "status": "pending"})
    client.post("/api/v1/tasks", json={"title": "Completada", "status": "completed"})
    response = client.get("/api/v1/tasks?status=completed")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Completada"


def test_list_tasks_filter_by_project(client):
    proj = client.post("/api/v1/projects", json={"name": "Proyecto"})
    project_id = proj.json()["id"]
    client.post(
        "/api/v1/tasks", json={"title": "T1", "project_id": project_id}
    )
    client.post("/api/v1/tasks", json={"title": "T2 sin proyecto"})
    response = client.get(f"/api/v1/tasks?project_id={project_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["project_id"] == project_id


def test_get_task(client):
    create = client.post("/api/v1/tasks", json={"title": "Buscar"})
    task_id = create.json()["id"]
    response = client.get(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["id"] == task_id


def test_get_task_not_found(client):
    response = client.get("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_task(client):
    create = client.post("/api/v1/tasks", json={"title": "Original"})
    task_id = create.json()["id"]
    response = client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"title": "Modificada", "status": "completed"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Modificada"
    assert data["status"] == "completed"


def test_complete_task(client):
    create = client.post("/api/v1/tasks", json={"title": "Completar"})
    task_id = create.json()["id"]
    response = client.post(f"/api/v1/tasks/{task_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["completed_at"] is not None


def test_reopen_task(client):
    create = client.post("/api/v1/tasks", json={"title": "Reabrir"})
    task_id = create.json()["id"]
    client.post(f"/api/v1/tasks/{task_id}/complete")
    response = client.post(f"/api/v1/tasks/{task_id}/reopen")
    assert response.status_code == 200
    assert response.json()["status"] == "pending"
    assert response.json()["completed_at"] is None


def test_delete_task(client):
    create = client.post("/api/v1/tasks", json={"title": "Eliminar"})
    task_id = create.json()["id"]
    response = client.delete(f"/api/v1/tasks/{task_id}")
    assert response.status_code == 204


def test_delete_task_not_found(client):
    response = client.delete("/api/v1/tasks/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_task_completing_does_not_change_project_status(client):
    """Completar o reabrir una tarea no cambia automáticamente el estado del proyecto (DATABASE.md 5.2)."""
    proj = client.post("/api/v1/projects", json={"name": "Proyecto"})
    project_id = proj.json()["id"]
    task = client.post(
        "/api/v1/tasks", json={"title": "Tarea", "project_id": project_id}
    )
    task_id = task.json()["id"]
    client.post(f"/api/v1/tasks/{task_id}/complete")
    project_response = client.get(f"/api/v1/projects/{project_id}")
    assert project_response.json()["status"] == "active"