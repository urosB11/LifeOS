"""Pruebas de Mind — MIND-002 (Spaces, Inbox, Canvas y Cards simples).

Criterios de aceptación cubiertos: SPEC MIND-002 §7 (1-11).
Todas las pruebas usan bases temporales (conftest).
"""

import json
import sqlite3

import pytest
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import IntegrityError

from app.modules.mind import service as mind_service
from app.modules.mind.models import (
    MindCanvas,
    MindCanvasHistory,
    MindCanvasNode,
    MindSpace,
    MindSpaceNote,
)
from app.modules.notes.models import Note

# --- Utilidades ------------------------------------------------------------


def _inbox(client):
    """Devuelve el Space Inbox (lo crea idempotentemente si hace falta)."""
    response = client.get("/api/v1/mind/inbox")
    assert response.status_code == 200, response.text
    return response.json()["space"]


def _create_space(client, name="Estudio", description=None):
    payload = {"name": name}
    if description is not None:
        payload["description"] = description
    response = client.post("/api/v1/mind/spaces", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def _create_canvas(client, space_id, title="Canvas de trabajo"):
    response = client.post(
        f"/api/v1/mind/spaces/{space_id}/canvases", json={"title": title}
    )
    assert response.status_code == 201, response.text
    return response.json()


def _create_card(client, canvas_id, content="Idea de prueba", x=10.0, y=20.0):
    response = client.post(
        f"/api/v1/mind/canvases/{canvas_id}/cards",
        json={"content": content, "x": x, "y": y},
    )
    assert response.status_code == 201, response.text
    return response.json()


# --- Inbox único -----------------------------------------------------------


def test_inbox_exists_and_is_unique(client):
    """Criterio 3: existe exactamente un Inbox tras el bootstrap."""
    first = client.get("/api/v1/mind/spaces")
    assert first.status_code == 200, first.text
    inboxes = [s for s in first.json() if s["is_inbox"]]
    assert len(inboxes) == 1
    assert inboxes[0]["name"] == "Inbox"

    # Repetir la consulta no crea un segundo Inbox.
    client.get("/api/v1/mind/inbox")
    client.get("/api/v1/mind/spaces?include_archived=true")
    again = client.get("/api/v1/mind/spaces")
    assert len([s for s in again.json() if s["is_inbox"]]) == 1


def test_database_rejects_a_second_inbox(client, db):
    """Criterio 3: la BD impide más de un Inbox (índice único parcial)."""
    _inbox(client)  # bootstrap: el primer Inbox ya existe

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.execute(
                text(
                    "INSERT INTO mind_spaces (id, name, description, is_inbox, "
                    "status, archived_at, created_at, updated_at) VALUES "
                    "('inbox-2', 'Otro Inbox', NULL, 1, 'active', NULL, "
                    "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
                )
            )


def test_inbox_cannot_be_renamed_archived_or_deleted(client):
    """Criterio 3: el Inbox no se renombra, archiva ni elimina desde la API."""
    inbox = _inbox(client)

    renamed = client.patch(
        f"/api/v1/mind/spaces/{inbox['id']}", json={"name": "Bandeja"}
    )
    assert renamed.status_code == 409, renamed.text

    archived = client.post(f"/api/v1/mind/spaces/{inbox['id']}/archive")
    assert archived.status_code == 409, archived.text

    deleted = client.delete(f"/api/v1/mind/spaces/{inbox['id']}")
    assert deleted.status_code in (404, 405), deleted.text


# --- Capturas del Inbox ----------------------------------------------------


def test_capture_creates_canonical_note_and_appears_in_inbox(client):
    """Criterio 4: capturar una idea crea una Note canónica y aparece en Inbox."""
    response = client.post(
        "/api/v1/mind/inbox/captures", json={"content": "Primera idea"}
    )
    assert response.status_code == 201, response.text
    note = response.json()
    assert note["id"]
    assert note["title"] == "Primera idea"  # título derivado del contenido
    assert note["content"] == "Primera idea"

    inbox = client.get("/api/v1/mind/inbox")
    assert inbox.status_code == 200
    captures = inbox.json()["captures"]
    assert len(captures) == 1
    assert captures[0]["id"] == note["id"]

    # La Note existe también en el API canónico de Notas (sin duplicar modelo).
    canonical = client.get(f"/api/v1/notes/{note['id']}")
    assert canonical.status_code == 200
    assert canonical.json()["content"] == "Primera idea"


def test_capture_keeps_explicit_title_and_rejects_blank_content(client):
    """Criterio 4: título opcional; el contenido es obligatorio."""
    response = client.post(
        "/api/v1/mind/inbox/captures",
        json={"title": "Mi título", "content": "Contenido con detalle"},
    )
    assert response.status_code == 201, response.text
    assert response.json()["title"] == "Mi título"

    blank = client.post("/api/v1/mind/inbox/captures", json={"content": "    "})
    assert blank.status_code == 422, blank.text

    missing = client.post("/api/v1/mind/inbox/captures", json={"title": "Solo"})
    assert missing.status_code == 422, missing.text


def test_capture_is_edited_through_canonical_notes_api(client):
    """Criterio 4: la captura del Inbox se edita con el API canónico de Notes."""
    note = client.post(
        "/api/v1/mind/inbox/captures", json={"content": "Borrador"}
    ).json()

    updated = client.patch(
        f"/api/v1/notes/{note['id']}",
        json={"title": "Editada", "content": "Contenido editado"},
    )
    assert updated.status_code == 200, updated.text

    captures = client.get("/api/v1/mind/inbox").json()["captures"]
    assert len(captures) == 1
    assert captures[0]["title"] == "Editada"
    assert captures[0]["content"] == "Contenido editado"


def test_capture_survives_a_new_session(client):
    """Criterio 5: la captura se conserva al reiniciar la aplicación."""
    from app.db.session import SessionLocal
    from app.modules.mind.repository import (
        MindCanvasRepository,
        MindNodeRepository,
        MindSpaceRepository,
    )
    from app.modules.mind.service import MindService
    from app.modules.notes.repository import (
        NoteLinkRepository,
        NoteRepository,
        TagRepository,
    )
    from app.modules.notes.service import NoteService
    from app.modules.projects.repository import ProjectRepository
    from app.modules.tasks.repository import TaskRepository

    def build(db):
        return MindService(
            space_repo=MindSpaceRepository(db),
            canvas_repo=MindCanvasRepository(db),
            node_repo=MindNodeRepository(db),
            note_service=NoteService(
                note_repo=NoteRepository(db),
                link_repo=NoteLinkRepository(db),
                tag_repo=TagRepository(db),
                project_repo=ProjectRepository(db),
                task_repo=TaskRepository(db),
                db=db,
            ),
            db=db,
        )

    with SessionLocal() as db:
        service = build(db)
        service.ensure_inbox()
        from app.modules.mind.schemas import MindCaptureCreate

        note = service.create_capture(MindCaptureCreate(content="Persistente"))
        db.commit()
        note_id = note.id

    # Nueva sesión: el contenido sigue en disco (no era estado en memoria).
    with SessionLocal() as db:
        service = build(db)
        inbox, captures = service.get_inbox()
        assert any(c.id == note_id for c in captures)
        assert inbox.is_inbox is True

        # Limpieza: la base global de tests no debe quedar con datos.
        db.execute(delete(Note).where(Note.id == note_id))
        db.execute(delete(MindSpaceNote).where(MindSpaceNote.note_id == note_id))
        db.commit()


# --- Spaces ----------------------------------------------------------------


def test_space_crud_rename_and_archive(client):
    """Criterio 2: se crea, lista, renombra y archiva un Space."""
    created = _create_space(client, "Estudio", "Notas de la materia")
    space_id = created["id"]
    assert created["name"] == "Estudio"
    assert created["description"] == "Notas de la materia"
    assert created["status"] == "active"
    assert created["is_inbox"] is False

    listed = client.get("/api/v1/mind/spaces").json()
    assert any(s["id"] == space_id for s in listed)

    renamed = client.patch(
        f"/api/v1/mind/spaces/{space_id}",
        json={"name": "Estudio avanzado", "description": "Actualizado"},
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["name"] == "Estudio avanzado"
    assert renamed.json()["description"] == "Actualizado"

    archived = client.post(f"/api/v1/mind/spaces/{space_id}/archive")
    assert archived.status_code == 200, archived.text
    assert archived.json()["status"] == "archived"
    assert archived.json()["archived_at"]

    active = client.get("/api/v1/mind/spaces").json()
    assert not any(s["id"] == space_id for s in active)

    with_archived = client.get("/api/v1/mind/spaces?include_archived=true").json()
    assert any(s["id"] == space_id for s in with_archived)

    restored = client.post(f"/api/v1/mind/spaces/{space_id}/restore")
    assert restored.status_code == 200, restored.text
    assert restored.json()["status"] == "active"
    assert restored.json()["archived_at"] is None


def test_space_requires_name(client):
    """Criterio 2: el nombre del Space es obligatorio."""
    response = client.post("/api/v1/mind/spaces", json={"name": "   "})
    assert response.status_code == 422, response.text


def test_unknown_space_returns_404(client):
    """Criterio 2: recursos inexistentes devuelven 404."""
    assert client.get("/api/v1/mind/spaces/no-existe").status_code == 404
    assert client.patch(
        "/api/v1/mind/spaces/no-existe", json={"name": "X"}
    ).status_code == 404


# --- Canvases --------------------------------------------------------------


def test_canvas_crud_and_archive(client):
    """Criterio 6: se crea, abre, renombra y archiva un Canvas en un Space."""
    space = _create_space(client)
    canvas = _create_canvas(client, space["id"], "Mapa inicial")
    canvas_id = canvas["id"]
    assert canvas["space_id"] == space["id"]
    assert canvas["status"] == "active"

    listed = client.get(f"/api/v1/mind/spaces/{space['id']}/canvases").json()
    assert [c["id"] for c in listed] == [canvas_id]

    fetched = client.get(f"/api/v1/mind/canvases/{canvas_id}")
    assert fetched.status_code == 200
    assert fetched.json()["title"] == "Mapa inicial"

    renamed = client.patch(
        f"/api/v1/mind/canvases/{canvas_id}",
        json={"title": "Mapa revisado", "description": "Con notas"},
    )
    assert renamed.status_code == 200, renamed.text
    assert renamed.json()["title"] == "Mapa revisado"

    archived = client.post(f"/api/v1/mind/canvases/{canvas_id}/archive")
    assert archived.status_code == 200, archived.text
    assert archived.json()["status"] == "archived"

    active = client.get(f"/api/v1/mind/spaces/{space['id']}/canvases").json()
    assert not any(c["id"] == canvas_id for c in active)

    restored = client.post(f"/api/v1/mind/canvases/{canvas_id}/restore")
    assert restored.status_code == 200, restored.text
    assert restored.json()["status"] == "active"


def test_archived_space_blocks_new_canvas_but_keeps_existing(client):
    """Criterio 6 y §2.2: archivar un Space no pierde sus Canvases."""
    space = _create_space(client)
    canvas = _create_canvas(client, space["id"])
    _create_card(client, canvas["id"], "Idea en el canvas")

    assert client.post(f"/api/v1/mind/spaces/{space['id']}/archive").status_code == 200

    blocked = client.post(
        f"/api/v1/mind/spaces/{space['id']}/canvases", json={"title": "Nuevo"}
    )
    assert blocked.status_code == 409, blocked.text

    canvases = client.get(
        f"/api/v1/mind/spaces/{space['id']}/canvases?include_archived=true"
    ).json()
    assert any(c["id"] == canvas["id"] for c in canvases)

    nodes = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()
    assert len(nodes) == 1
    assert nodes[0]["note"]["content"] == "Idea en el canvas"


# --- Cards -----------------------------------------------------------------


def test_create_card_and_edit_its_content(client):
    """Criterio 7: se crea una Card de texto y se puede editar."""
    space = _create_space(client)
    canvas = _create_canvas(client, space["id"])
    node = _create_card(client, canvas["id"], "Idea inicial")

    assert node["note"]["content"] == "Idea inicial"
    assert node["note"]["title"] == "Idea inicial"
    assert node["x"] == 10.0
    assert node["y"] == 20.0

    # El contenido se edita en la Note canónica y la Card lo refleja.
    updated = client.patch(
        f"/api/v1/notes/{node['note_id']}",
        json={"title": "Idea editada", "content": "Idea corregida"},
    )
    assert updated.status_code == 200, updated.text

    nodes = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()
    assert len(nodes) == 1
    assert nodes[0]["note"]["title"] == "Idea editada"
    assert nodes[0]["note"]["content"] == "Idea corregida"


def test_card_position_persists(client):
    """Criterio 8: la posición de la Card se guarda y se recupera."""
    space = _create_space(client)
    canvas = _create_canvas(client, space["id"])
    node = _create_card(client, canvas["id"], x=5.0, y=6.0)

    moved = client.patch(
        f"/api/v1/mind/canvases/{canvas['id']}/nodes/{node['id']}",
        json={"x": 320.5, "y": 128.0},
    )
    assert moved.status_code == 200, moved.text
    assert moved.json()["x"] == 320.5
    assert moved.json()["y"] == 128.0

    reloaded = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()
    assert len(reloaded) == 1
    assert reloaded[0]["x"] == 320.5
    assert reloaded[0]["y"] == 128.0


def test_removing_a_card_does_not_delete_the_note(client):
    """Criterio 9: quitar una Card no elimina su Note."""
    space = _create_space(client)
    canvas = _create_canvas(client, space["id"])
    node = _create_card(client, canvas["id"], "No perder este texto")

    removed = client.delete(
        f"/api/v1/mind/canvases/{canvas['id']}/nodes/{node['id']}"
    )
    assert removed.status_code == 204, removed.text

    assert client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json() == []
    note = client.get(f"/api/v1/notes/{node['note_id']}")
    assert note.status_code == 200
    assert note.json()["content"] == "No perder este texto"


def test_deleting_a_note_removes_mind_references(client, db):
    """Criterio 10: eliminar la Note no deja referencias Mind huérfanas."""
    capture = client.post(
        "/api/v1/mind/inbox/captures", json={"content": "Captura y Card"}
    ).json()
    space = _create_space(client)
    canvas = _create_canvas(client, space["id"])
    node = _create_card(client, canvas["id"], "Vinculada a la captura")
    assert node["note_id"]

    # La misma Note representada en un Canvas y miembro del Inbox.
    attached = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/nodes",
        json={"note_id": capture["id"], "x": 1.0, "y": 2.0},
    )
    assert attached.status_code == 201, attached.text

    deleted = client.delete(f"/api/v1/notes/{capture['id']}")
    assert deleted.status_code == 204, deleted.text

    nodes = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()
    assert all(n["note_id"] != capture["id"] for n in nodes)

    memberships = db.execute(
        select(MindSpaceNote).where(MindSpaceNote.note_id == capture["id"])
    ).scalars().all()
    assert memberships == []

    orphan_nodes = db.execute(
        select(MindCanvasNode).where(MindCanvasNode.note_id == capture["id"])
    ).scalars().all()
    assert orphan_nodes == []

    assert client.get("/api/v1/mind/inbox").json()["captures"] == []


def test_same_note_can_be_represented_in_several_canvases(client):
    """Criterio 4/§3: el contenido no se duplica ni se restringe a un Canvas."""
    capture = client.post(
        "/api/v1/mind/inbox/captures", json={"content": "Idea reutilizable"}
    ).json()
    space = _create_space(client)
    canvas_a = _create_canvas(client, space["id"], "Canvas A")
    canvas_b = _create_canvas(client, space["id"], "Canvas B")

    first = client.post(
        f"/api/v1/mind/canvases/{canvas_a['id']}/nodes",
        json={"note_id": capture["id"], "x": 0.0, "y": 0.0},
    )
    second = client.post(
        f"/api/v1/mind/canvases/{canvas_b['id']}/nodes",
        json={"note_id": capture["id"], "x": 40.0, "y": 60.0},
    )
    assert first.status_code == 201, first.text
    assert second.status_code == 201, second.text
    assert first.json()["note_id"] == second.json()["note_id"] == capture["id"]
    assert second.json()["x"] == 40.0

    # La Note canónica sigue siendo una sola.
    notes = client.get("/api/v1/notes").json()
    matching = [n for n in notes if n["id"] == capture["id"]]
    assert len(matching) == 1


def test_attaching_the_same_note_twice_conflicts(client):
    """Una Note no puede tener dos representaciones en el mismo Canvas."""
    capture = client.post(
        "/api/v1/mind/inbox/captures", json={"content": "Una sola vez"}
    ).json()
    space = _create_space(client)
    canvas = _create_canvas(client, space["id"])

    first = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/nodes",
        json={"note_id": capture["id"], "x": 0.0, "y": 0.0},
    )
    assert first.status_code == 201, first.text

    second = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/nodes",
        json={"note_id": capture["id"], "x": 10.0, "y": 10.0},
    )
    assert second.status_code == 409, second.text


def test_archived_canvas_blocks_editing(client):
    """Un Canvas archivado no se edita hasta restaurarlo."""
    space = _create_space(client)
    canvas = _create_canvas(client, space["id"])
    node = _create_card(client, canvas["id"])

    assert client.post(f"/api/v1/mind/canvases/{canvas['id']}/archive").status_code == 200

    blocked_card = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/cards",
        json={"content": "No permitido", "x": 0.0, "y": 0.0},
    )
    assert blocked_card.status_code == 409, blocked_card.text

    blocked_move = client.patch(
        f"/api/v1/mind/canvases/{canvas['id']}/nodes/{node['id']}",
        json={"x": 1.0, "y": 1.0},
    )
    assert blocked_move.status_code == 409, blocked_move.text

    assert client.post(f"/api/v1/mind/canvases/{canvas['id']}/restore").status_code == 200
    allowed = client.patch(
        f"/api/v1/mind/canvases/{canvas['id']}/nodes/{node['id']}",
        json={"x": 1.0, "y": 1.0},
    )
    assert allowed.status_code == 200, allowed.text


def test_node_of_another_canvas_is_not_found(client):
    """Una Card de otro Canvas no se modifica desde este Canvas."""
    space = _create_space(client)
    canvas_a = _create_canvas(client, space["id"], "A")
    canvas_b = _create_canvas(client, space["id"], "B")
    node = _create_card(client, canvas_a["id"])

    response = client.patch(
        f"/api/v1/mind/canvases/{canvas_b['id']}/nodes/{node['id']}",
        json={"x": 5.0, "y": 5.0},
    )
    assert response.status_code == 404, response.text


# --- Exportación y backup --------------------------------------------------


def test_export_includes_mind_data_with_ids_and_references(client):
    """Criterio 11: la exportación JSON incluye los datos de Mind."""
    space = _create_space(client, "Espacio exportable")
    canvas = _create_canvas(client, space["id"], "Canvas exportable")
    node = _create_card(client, canvas["id"], "Contenido exportable")
    capture = client.post(
        "/api/v1/mind/inbox/captures", json={"content": "Captura exportable"}
    ).json()

    response = client.get("/api/v1/export")
    assert response.status_code == 200, response.text
    data = response.json()

    for key in (
        "mind_spaces",
        "mind_canvases",
        "mind_space_notes",
        "mind_canvas_nodes",
    ):
        assert key in data, f"Falta la clave {key} en la exportación"
        assert isinstance(data[key], list)

    spaces = {s["id"]: s for s in data["mind_spaces"]}
    assert space["id"] in spaces
    assert spaces[space["id"]]["name"] == "Espacio exportable"
    assert any(s["is_inbox"] for s in data["mind_spaces"])

    canvases = {c["id"]: c for c in data["mind_canvases"]}
    assert canvas["id"] in canvases
    assert canvases[canvas["id"]]["space_id"] == space["id"]

    nodes = {n["id"]: n for n in data["mind_canvas_nodes"]}
    assert node["id"] in nodes
    assert nodes[node["id"]]["note_id"] == node["note_id"]
    assert nodes[node["id"]]["x"] == 10.0

    memberships = {
        (m["space_id"], m["note_id"]) for m in data["mind_space_notes"]
    }
    inbox_id = next(s["id"] for s in data["mind_spaces"] if s["is_inbox"])
    assert (inbox_id, capture["id"]) in memberships


def test_backup_file_contains_mind_tables(tmp_path):
    """Criterio 11: el backup SQLite incluye las tablas de Mind."""
    from app.modules.data_service import backup_sqlite_to_file

    dest = tmp_path / "backup-mind.db"
    backup_sqlite_to_file(str(dest))
    assert dest.exists()

    conn = sqlite3.connect(str(dest))
    try:
        tables = {
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        for expected in (
            "mind_spaces",
            "mind_canvases",
            "mind_space_notes",
            "mind_canvas_nodes",
        ):
            assert expected in tables, f"Falta tabla {expected} en el backup"
    finally:
        conn.close()


def test_restore_roundtrip_preserves_mind_data(client):
    """Criterio 11: backup y restauración conservan los datos de Mind.

    Usa el engine global, aislado en un directorio temporal por el conftest
    (nunca la base personal).
    """
    from app.db.session import SessionLocal, engine

    with SessionLocal() as db:
        space = MindSpace(name="Space restaurado", is_inbox=False, status="active")
        db.add(space)
        db.flush()
        note = Note(title="Nota restaurada", content="Contenido restaurado")
        db.add(note)
        db.flush()
        canvas = MindCanvas(space_id=space.id, title="Canvas restaurado", status="active")
        db.add(canvas)
        db.flush()
        db.add(
            MindCanvasNode(
                canvas_id=canvas.id, note_id=note.id, x=11.0, y=22.0, z_index=0
            )
        )
        db.commit()
        space_id, canvas_id, note_id = space.id, canvas.id, note.id

    try:
        backup = client.get("/api/v1/backup")
        assert backup.status_code == 200, backup.text
        backup_bytes = backup.content

        with SessionLocal() as db:
            db.execute(delete(MindCanvasNode))
            db.execute(delete(MindCanvas))
            db.execute(delete(MindSpace).where(MindSpace.id == space_id))
            db.commit()

        restored = client.post(
            "/api/v1/restore",
            content=backup_bytes,
            headers={"Content-Type": "application/octet-stream"},
        )
        assert restored.status_code == 200, restored.text
        assert restored.json()["restored"] is True

        with SessionLocal() as db:
            spaces = db.execute(
                select(MindSpace).where(MindSpace.id == space_id)
            ).scalars().all()
            assert len(spaces) == 1
            assert spaces[0].name == "Space restaurado"

            canvases = db.execute(
                select(MindCanvas).where(MindCanvas.id == canvas_id)
            ).scalars().all()
            assert len(canvases) == 1

            nodes = db.execute(
                select(MindCanvasNode).where(MindCanvasNode.note_id == note_id)
            ).scalars().all()
            assert len(nodes) == 1
            assert nodes[0].x == 11.0
            assert nodes[0].y == 22.0
    finally:
        with SessionLocal() as db:
            db.execute(delete(MindCanvasNode))
            db.execute(delete(MindCanvas).where(MindCanvas.id == canvas_id))
            db.execute(delete(MindSpace).where(MindSpace.id == space_id))
            db.execute(delete(Note).where(Note.id == note_id))
            db.commit()
        engine.dispose()


# --- Canvas interactivo: spatially persistence and history -----------------


def _canvas_with_cards(client, count=2):
    space = _create_space(client, name="Canvas interactivo")
    canvas = _create_canvas(client, space["id"], title="Canvas reversible")
    cards = [
        _create_card(client, canvas["id"], content=f"Card {index}", x=index * 100.0)
        for index in range(count)
    ]
    return canvas, cards


def test_spatial_action_is_atomic_and_idempotent(client, db):
    canvas, cards = _canvas_with_cards(client)
    payload = {
        "action_type": "move",
        "nodes": [
            {"id": cards[0]["id"], "x": 55.0, "y": 66.0},
            {"id": cards[1]["id"], "x": 155.0, "y": 166.0},
        ],
    }
    headers = {"Idempotency-Key": "spatial-move-1"}

    response = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json=payload,
        headers=headers,
    )
    assert response.status_code == 200, response.text
    assert response.json()["can_undo"] is True

    nodes = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()
    positions = {node["id"]: (node["x"], node["y"]) for node in nodes}
    assert positions[cards[0]["id"]] == (55.0, 66.0)
    assert positions[cards[1]["id"]] == (155.0, 166.0)

    replay = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json=payload,
        headers=headers,
    )
    assert replay.status_code == 200, replay.text
    history_count = db.execute(
        select(func.count(MindCanvasHistory.id)).where(
            MindCanvasHistory.canvas_id == canvas["id"]
        )
    ).scalar_one()
    assert history_count == 3  # una creación de Card por Card + una acción grupal

    changed_payload = {
        **payload,
        "nodes": [{"id": cards[0]["id"], "x": 999.0, "y": 66.0}],
    }
    conflict = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json=changed_payload,
        headers=headers,
    )
    assert conflict.status_code == 409, conflict.text


def test_spatial_group_rejects_foreign_node_without_partial_changes(client):
    canvas, cards = _canvas_with_cards(client)
    response = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "move",
            "nodes": [
                {"id": cards[0]["id"], "x": 300.0, "y": 400.0},
                {"id": "missing-node", "x": 500.0, "y": 600.0},
            ],
        },
        headers={"Idempotency-Key": "spatial-invalid"},
    )
    assert response.status_code == 404, response.text
    node = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()[0]
    assert (node["x"], node["y"]) != (300.0, 400.0)


def test_undo_and_redo_restore_spatial_state_and_retry_safely(client):
    canvas, cards = _canvas_with_cards(client, count=1)
    card = cards[0]
    moved = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "move",
            "nodes": [{"id": card["id"], "x": 321.0, "y": 654.0}],
        },
        headers={"Idempotency-Key": "move-for-undo"},
    )
    assert moved.status_code == 200, moved.text

    history = client.get(f"/api/v1/mind/canvases/{canvas['id']}/history").json()
    action_id = history["undo_action_id"]
    undo_headers = {"Idempotency-Key": "undo-1"}
    undo = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/history/undo",
        json={"expected_action_id": action_id},
        headers=undo_headers,
    )
    assert undo.status_code == 200, undo.text
    assert undo.json()["can_redo"] is True
    node = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()[0]
    assert (node["x"], node["y"]) == (card["x"], card["y"])

    retry = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/history/undo",
        json={"expected_action_id": action_id},
        headers=undo_headers,
    )
    assert retry.status_code == 200, retry.text
    node = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()[0]
    assert (node["x"], node["y"]) == (card["x"], card["y"])

    redo = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/history/redo",
        json={"expected_action_id": action_id},
        headers={"Idempotency-Key": "redo-1"},
    )
    assert redo.status_code == 200, redo.text
    node = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()[0]
    assert (node["x"], node["y"]) == (321.0, 654.0)


def test_stale_expected_action_is_rejected_without_changing_state(client):
    canvas, cards = _canvas_with_cards(client, count=1)
    card = cards[0]
    first = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "move",
            "nodes": [{"id": card["id"], "x": 100.0, "y": 100.0}],
        },
        headers={"Idempotency-Key": "stale-first"},
    )
    assert first.status_code == 200, first.text
    second = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "move",
            "nodes": [{"id": card["id"], "x": 200.0, "y": 200.0}],
        },
        headers={"Idempotency-Key": "stale-second"},
    )
    assert second.status_code == 200, second.text

    stale = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/history/undo",
        json={"expected_action_id": first.json()["undo_action_id"]},
        headers={"Idempotency-Key": "stale-undo"},
    )
    assert stale.status_code == 409, stale.text
    node = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()[0]
    assert (node["x"], node["y"]) == (200.0, 200.0)


def test_invalid_snapshot_returns_conflict_without_partial_changes(client, db):
    canvas, cards = _canvas_with_cards(client, count=2)
    edge = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/edges",
        json={
            "source_node_id": cards[0]["id"],
            "target_node_id": cards[1]["id"],
        },
        headers={"Idempotency-Key": "invalid-snapshot-edge"},
    )
    assert edge.status_code == 201, edge.text
    action_id = client.get(
        f"/api/v1/mind/canvases/{canvas['id']}/history"
    ).json()["undo_action_id"]
    row = db.execute(
        select(MindCanvasHistory).where(MindCanvasHistory.id == action_id)
    ).scalar_one()
    envelope = json.loads(row.snapshot_json)
    source_id, target_id = sorted(card["id"] for card in cards)
    envelope["state"]["edges"] = [
        {
            "id": "invalid-anchor-edge",
            "canvas_id": canvas["id"],
            "source_node_id": source_id,
            "target_node_id": target_id,
            "source_anchor": 99,
            "target_anchor": 0,
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    ]
    row.snapshot_json = json.dumps(envelope)
    db.flush()

    undo = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/history/undo",
        json={"expected_action_id": action_id},
        headers={"Idempotency-Key": "invalid-snapshot-undo"},
    )
    assert undo.status_code == 409, undo.text
    assert len(client.get(f"/api/v1/mind/canvases/{canvas['id']}/edges").json()) == 1


def test_pruned_history_keeps_idempotency_receipt(client, db, monkeypatch):
    monkeypatch.setattr(mind_service, "HISTORY_LIMIT", 2)
    space = _create_space(client, name="Space idempotente")
    canvas = _create_canvas(client, space["id"], title="Canvas idempotente")
    card_payload = {"content": "Card idempotente", "x": 1.0, "y": 2.0}
    created = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/cards",
        json=card_payload,
        headers={"Idempotency-Key": "card-receipt"},
    )
    assert created.status_code == 201, created.text
    card = created.json()

    for index in range(2):
        moved = client.post(
            f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
            json={
                "action_type": "move",
                "nodes": [
                    {"id": card["id"], "x": 10.0 + index, "y": 20.0 + index}
                ],
            },
            headers={"Idempotency-Key": f"move-receipt-{index}"},
        )
        assert moved.status_code == 200, moved.text

    replay = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/cards",
        json=card_payload,
        headers={"Idempotency-Key": "card-receipt"},
    )
    assert replay.status_code == 201, replay.text
    assert replay.json()["id"] == card["id"]
    assert len(client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()) == 1

    rows = db.execute(
        select(MindCanvasHistory).where(
            MindCanvasHistory.canvas_id == canvas["id"]
        )
    ).scalars().all()
    active_rows = [
        row
        for row in rows
        if row.action_type != mind_service.HISTORY_RECEIPT_ACTION
    ]
    assert len(active_rows) <= 2
    assert any(
        row.action_type == mind_service.HISTORY_RECEIPT_ACTION for row in rows
    )


def test_new_action_after_undo_discards_redo_branch(client):
    canvas, cards = _canvas_with_cards(client, count=1)
    card = cards[0]
    first = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "move",
            "nodes": [{"id": card["id"], "x": 100.0, "y": 100.0}],
        },
        headers={"Idempotency-Key": "move-first"},
    )
    action_id = first.json()["undo_action_id"]
    client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/history/undo",
        json={"expected_action_id": action_id},
        headers={"Idempotency-Key": "undo-first"},
    )
    second = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "move",
            "nodes": [{"id": card["id"], "x": 200.0, "y": 200.0}],
        },
        headers={"Idempotency-Key": "move-second"},
    )
    assert second.status_code == 200, second.text
    assert second.json()["can_redo"] is False


def test_edges_are_non_directed_unique_and_reversible(client):
    canvas, cards = _canvas_with_cards(client)
    source = cards[0]["id"]
    target = cards[1]["id"]
    created = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/edges",
        json={"source_node_id": source, "target_node_id": target},
        headers={"Idempotency-Key": "edge-create"},
    )
    assert created.status_code == 201, created.text

    duplicate = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/edges",
        json={"source_node_id": target, "target_node_id": source},
        headers={"Idempotency-Key": "edge-duplicate"},
    )
    assert duplicate.status_code == 409, duplicate.text

    history = client.get(f"/api/v1/mind/canvases/{canvas['id']}/history").json()
    undo = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/history/undo",
        json={"expected_action_id": history["undo_action_id"]},
        headers={"Idempotency-Key": "edge-undo"},
    )
    assert undo.status_code == 200, undo.text
    assert client.get(f"/api/v1/mind/canvases/{canvas['id']}/edges").json() == []


def test_reorder_normalizes_all_z_indexes(client):
    canvas, cards = _canvas_with_cards(client, count=3)
    response = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "reorder",
            "nodes": [{"id": cards[0]["id"], "z_index": 2}],
        },
        headers={"Idempotency-Key": "reorder-front"},
    )
    assert response.status_code == 200, response.text
    nodes = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()
    assert sorted(node["z_index"] for node in nodes) == [0, 1, 2]


def test_reorder_uses_created_at_and_id_as_stable_tie_breakers(client, db):
    canvas, cards = _canvas_with_cards(client, count=3)
    db.execute(
        MindCanvasNode.__table__.update()
        .where(MindCanvasNode.canvas_id == canvas["id"])
        .values(created_at="2026-01-01T00:00:00Z")
    )
    db.flush()
    desired = [
        card["id"]
        for card in sorted(cards, key=lambda item: item["id"], reverse=True)
    ]

    response = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "reorder",
            "nodes": [
                {"id": node_id, "z_index": index}
                for index, node_id in enumerate(desired)
            ],
        },
        headers={"Idempotency-Key": "reorder-complete"},
    )
    assert response.status_code == 200, response.text
    nodes = client.get(f"/api/v1/mind/canvases/{canvas['id']}/nodes").json()
    assert [node["id"] for node in nodes] == desired
    assert [node["z_index"] for node in nodes] == [0, 1, 2]


def test_spatial_action_accepts_more_than_one_hundred_cards(client, db):
    space = _create_space(client, name="Space amplio")
    canvas = _create_canvas(client, space["id"], title="Canvas amplio")
    notes = [
        Note(
            id=f"wide-note-{index:03d}",
            title=f"Nota {index}",
            content="Contenido",
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        for index in range(101)
    ]
    nodes = [
        MindCanvasNode(
            id=f"wide-node-{index:03d}",
            canvas_id=canvas["id"],
            note_id=note.id,
            x=float(index),
            y=0.0,
            z_index=index,
            created_at="2026-01-01T00:00:00Z",
            updated_at="2026-01-01T00:00:00Z",
        )
        for index, note in enumerate(notes)
    ]
    db.add_all([*notes, *nodes])
    db.flush()

    response = client.post(
        f"/api/v1/mind/canvases/{canvas['id']}/spatial-actions",
        json={
            "action_type": "move",
            "nodes": [
                {"id": node.id, "x": float(index + 1), "y": 10.0}
                for index, node in enumerate(nodes)
            ],
        },
        headers={"Idempotency-Key": "move-over-one-hundred"},
    )
    assert response.status_code == 200, response.text


def test_node_update_can_restore_default_dimensions(client):
    canvas, cards = _canvas_with_cards(client, count=1)
    response = client.patch(
        f"/api/v1/mind/canvases/{canvas['id']}/nodes/{cards[0]['id']}",
        json={"width": None, "height": None},
    )
    assert response.status_code == 200, response.text
    assert response.json()["width"] is None
    assert response.json()["height"] is None


def test_deleting_note_clears_affected_canvas_history(client):
    canvas, cards = _canvas_with_cards(client, count=1)
    impact = client.get(
        f"/api/v1/mind/notes/{cards[0]['note_id']}/delete-impact"
    )
    assert impact.status_code == 200, impact.text
    assert impact.json()["cleared_history_actions"] >= 1

    deleted = client.delete(f"/api/v1/notes/{cards[0]['note_id']}")
    assert deleted.status_code == 204, deleted.text
    history = client.get(f"/api/v1/mind/canvases/{canvas['id']}/history").json()
    assert history["can_undo"] is False
    assert history["can_redo"] is False


def test_deleting_note_clears_history_that_could_restore_removed_card(client):
    canvas, cards = _canvas_with_cards(client, count=1)
    removed = client.delete(
        f"/api/v1/mind/canvases/{canvas['id']}/nodes/{cards[0]['id']}"
    )
    assert removed.status_code == 204, removed.text

    impact = client.get(
        f"/api/v1/mind/notes/{cards[0]['note_id']}/delete-impact"
    )
    assert impact.status_code == 200, impact.text
    assert impact.json()["affected_canvases"] == 1
    assert impact.json()["cleared_history_actions"] >= 1

    deleted = client.delete(f"/api/v1/notes/{cards[0]['note_id']}")
    assert deleted.status_code == 204, deleted.text
    history = client.get(f"/api/v1/mind/canvases/{canvas['id']}/history").json()
    assert history["can_undo"] is False
    assert history["can_redo"] is False


def test_database_rejects_edge_with_node_from_another_canvas(client, db):
    first_canvas, first_cards = _canvas_with_cards(client, count=1)
    second_canvas, second_cards = _canvas_with_cards(client, count=1)
    source = first_cards[0]["id"]
    target = second_cards[0]["id"]
    if source > target:
        source, target = target, source

    with pytest.raises(IntegrityError):
        with db.begin_nested():
            db.execute(
                text(
                    "INSERT INTO mind_canvas_edges "
                    "(id, canvas_id, source_node_id, target_node_id, "
                    "source_anchor, target_anchor, created_at, updated_at) "
                    "VALUES ('cross-edge', :canvas_id, :source, :target, 0, 0, "
                    "'2026-01-01T00:00:00Z', '2026-01-01T00:00:00Z')"
                ),
                {
                    "canvas_id": first_canvas["id"],
                    "source": source,
                    "target": target,
                },
            )
