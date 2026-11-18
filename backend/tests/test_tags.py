"""Pruebas de API e integración para Etiquetas."""




def test_create_tag(client):
    response = client.post(
        "/api/v1/notes/tags",
        json={"name": "Trabajo"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Trabajo"
    assert "id" in data
    assert "normalized_name" in data
    assert data["normalized_name"] == "trabajo"


def test_create_tag_reuses_existing(client):
    """No se permiten duplicados por mayúsculas o espacios (normalización)."""
    r1 = client.post("/api/v1/notes/tags", json={"name": "Trabajo"})
    assert r1.status_code == 201

    # Mismo nombre con mayúsculas diferentes -> reutiliza, no duplica
    r2 = client.post("/api/v1/notes/tags", json={"name": "  TRABAJO  "})
    assert r2.status_code == 201
    assert r2.json()["id"] == r1.json()["id"]  # misma etiqueta

    # Listar tags -> solo uno
    r = client.get("/api/v1/notes/tags")
    assert len(r.json()) == 1


def test_create_tag_empty_name_rejected(client):
    response = client.post("/api/v1/notes/tags", json={"name": "   "})
    assert response.status_code == 422


def test_list_tags(client):
    client.post("/api/v1/notes/tags", json={"name": "Personal"})
    client.post("/api/v1/notes/tags", json={"name": "Urgente"})
    response = client.get("/api/v1/notes/tags")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_tag(client):
    create = client.post("/api/v1/notes/tags", json={"name": "Importante"})
    tag_id = create.json()["id"]
    response = client.get(f"/api/v1/notes/tags/{tag_id}")
    assert response.status_code == 200
    assert response.json()["id"] == tag_id


def test_get_tag_not_found(client):
    response = client.get("/api/v1/notes/tags/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_note_tag_link_and_filter(client):
    """Asignar etiqueta a nota y filtrar notas por etiqueta."""
    tag = client.post("/api/v1/notes/tags", json={"name": "Ideas"})
    tag_id = tag.json()["id"]

    note1 = client.post(
        "/api/v1/notes", json={"title": "Nota 1", "content": "Idea A"}
    )
    note1_id = note1.json()["id"]

    client.post(
        "/api/v1/notes", json={"title": "Nota 2", "content": "Idea B"}
    )

    # Asignar etiqueta a nota1
    r = client.post(f"/api/v1/notes/{note1_id}/tags", json={"id": tag_id})
    assert r.status_code == 204

    # Filtrar notas por etiqueta
    r = client.get(f"/api/v1/notes/tags/{tag_id}/notes")
    assert r.status_code == 200
    notes = r.json()
    assert len(notes) == 1
    assert notes[0]["id"] == note1_id

    # Quitar etiqueta
    r = client.delete(f"/api/v1/notes/{note1_id}/tags/{tag_id}")
    assert r.status_code == 204

    r = client.get(f"/api/v1/notes/tags/{tag_id}/notes")
    assert len(r.json()) == 0


def test_note_deletion_removes_tag_links_not_tag(client):
    """Eliminar una nota quita sus asignaciones de etiqueta, no la etiqueta compartida."""
    tag = client.post("/api/v1/notes/tags", json={"name": "Compartida"})
    tag_id = tag.json()["id"]

    note = client.post("/api/v1/notes", json={"title": "Nota"})
    note_id = note.json()["id"]

    client.post(f"/api/v1/notes/{note_id}/tags", json={"id": tag_id})

    # Eliminar nota
    r = client.delete(f"/api/v1/notes/{note_id}")
    assert r.status_code == 204

    # La etiqueta sigue existiendo
    r = client.get(f"/api/v1/notes/tags/{tag_id}")
    assert r.status_code == 200