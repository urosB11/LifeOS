"""Pruebas de API e integración para Notas, vínculos y etiquetas."""




def test_create_note(client):
    response = client.post(
        "/api/v1/notes",
        json={"title": "Nota de prueba", "content": "Contenido de la nota"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["title"] == "Nota de prueba"
    assert data["content"] == "Contenido de la nota"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_create_note_empty_title_rejected(client):
    response = client.post("/api/v1/notes", json={"title": "   "})
    assert response.status_code == 422


def test_list_notes(client):
    client.post("/api/v1/notes", json={"title": "Nota 1", "content": "A"})
    client.post("/api/v1/notes", json={"title": "Nota 2", "content": "B"})
    response = client.get("/api/v1/notes")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_list_notes_search(client):
    client.post("/api/v1/notes", json={"title": "Manzana", "content": "Fruta roja"})
    client.post("/api/v1/notes", json={"title": "Banana", "content": "Fruta amarilla"})
    response = client.get("/api/v1/notes?search=Manzana")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Manzana"


def test_get_note(client):
    create = client.post("/api/v1/notes", json={"title": "Buscar nota"})
    note_id = create.json()["id"]
    response = client.get(f"/api/v1/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["id"] == note_id
    assert response.json()["title"] == "Buscar nota"


def test_get_note_not_found(client):
    response = client.get("/api/v1/notes/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_update_note(client):
    create = client.post("/api/v1/notes", json={"title": "Original"})
    note_id = create.json()["id"]
    response = client.patch(
        f"/api/v1/notes/{note_id}",
        json={"title": "Modificada", "content": "Nuevo contenido"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Modificada"
    assert data["content"] == "Nuevo contenido"


def test_delete_note(client):
    create = client.post("/api/v1/notes", json={"title": "Eliminar"})
    note_id = create.json()["id"]
    response = client.delete(f"/api/v1/notes/{note_id}")
    assert response.status_code == 204


def test_delete_note_not_found(client):
    response = client.delete("/api/v1/notes/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_note_links_project_and_task(client):
    """Una nota puede vincularse a un proyecto y una tarea; se ven desde ambos lados."""
    proj = client.post("/api/v1/projects", json={"name": "Proyecto para nota"})
    project_id = proj.json()["id"]

    task = client.post(
        "/api/v1/tasks", json={"title": "Tarea para nota", "project_id": project_id}
    )
    task_id = task.json()["id"]

    note = client.post(
        "/api/v1/notes", json={"title": "Nota vinculada", "content": "Contenido"}
    )
    note_id = note.json()["id"]

    # Vincular proyecto
    r = client.post(
        f"/api/v1/notes/{note_id}/projects", json={"id": project_id}
    )
    assert r.status_code == 204, r.text

    # Vincular tarea
    r = client.post(
        f"/api/v1/notes/{note_id}/tasks", json={"id": task_id}
    )
    assert r.status_code == 204, r.text

    # Consultar proyectos de la nota
    r = client.get(f"/api/v1/notes/{note_id}/projects")
    assert r.status_code == 200
    projects = r.json()
    assert len(projects) == 1
    assert projects[0]["id"] == project_id

    # Consultar tareas de la nota
    r = client.get(f"/api/v1/notes/{note_id}/tasks")
    assert r.status_code == 200
    tasks_list = r.json()
    assert len(tasks_list) == 1
    assert tasks_list[0]["id"] == task_id

    # Quitar vínculo proyecto
    r = client.delete(f"/api/v1/notes/{note_id}/projects/{project_id}")
    assert r.status_code == 204

    r = client.get(f"/api/v1/notes/{note_id}/projects")
    assert len(r.json()) == 0


def test_note_links_nonexistent_project_rejected(client):
    note = client.post("/api/v1/notes", json={"title": "Nota"})
    note_id = note.json()["id"]
    r = client.post(
        f"/api/v1/notes/{note_id}/projects",
        json={"id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code == 404


def test_note_survives_project_deletion(client):
    """Eliminar un proyecto no elimina la nota, solo quita el vínculo (DATABASE.md 5.4)."""
    proj = client.post("/api/v1/projects", json={"name": "Proyecto padre"})
    project_id = proj.json()["id"]

    note = client.post(
        "/api/v1/notes", json={"title": "Nota independiente"}
    )
    note_id = note.json()["id"]

    client.post(
        f"/api/v1/notes/{note_id}/projects", json={"id": project_id}
    )

    # Eliminar proyecto (no tiene tareas)
    r = client.delete(f"/api/v1/projects/{project_id}")
    assert r.status_code == 204

    # La nota sigue existiendo
    r = client.get(f"/api/v1/notes/{note_id}")
    assert r.status_code == 200
    assert r.json()["title"] == "Nota independiente"

    # El vínculo se quitó
    r = client.get(f"/api/v1/notes/{note_id}/projects")
    assert len(r.json()) == 0


def test_note_survives_task_deletion(client):
    """Eliminar una tarea no elimina la nota, solo quita el vínculo (DATABASE.md 5.5)."""
    task = client.post("/api/v1/tasks", json={"title": "Tarea"})
    task_id = task.json()["id"]

    note = client.post(
        "/api/v1/notes", json={"title": "Nota vinculada a tarea"}
    )
    note_id = note.json()["id"]

    client.post(f"/api/v1/notes/{note_id}/tasks", json={"id": task_id})

    # Eliminar tarea
    r = client.delete(f"/api/v1/tasks/{task_id}")
    assert r.status_code == 204

    # La nota sigue existiendo
    r = client.get(f"/api/v1/notes/{note_id}")
    assert r.status_code == 200

    # El vínculo se quitó
    r = client.get(f"/api/v1/notes/{note_id}/tasks")
    assert len(r.json()) == 0