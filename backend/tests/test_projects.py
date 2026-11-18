"""Pruebas de API e integración para Proyectos."""

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