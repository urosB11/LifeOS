"""Rutas API de Mind (MIND-002/003): Spaces, Inbox, Canvases, Cards y Edges."""

from fastapi import APIRouter, Depends, status

from app.db.session import get_db
from app.modules.mind.repository import (
    MindCanvasRepository,
    MindEdgeRepository,
    MindNodeRepository,
    MindSpaceRepository,
)
from app.modules.mind.schemas import (
    MindCanvasCreate,
    MindCanvasOut,
    MindCanvasUpdate,
    MindCaptureCreate,
    MindCardCreate,
    MindEdgeCreate,
    MindEdgeOut,
    MindHistoryOut,
    MindHistoryTransition,
    MindInboxOut,
    MindNodeAttach,
    MindNodeOut,
    MindNodeUpdate,
    MindSpaceCreate,
    MindSpaceOut,
    MindSpaceUpdate,
)
from app.modules.mind.service import MindService
from app.modules.notes.repository import (
    NoteLinkRepository,
    NoteRepository,
    TagRepository,
)
from app.modules.notes.schemas import NoteOut
from app.modules.notes.service import NoteService
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository

router = APIRouter(prefix="/mind", tags=["mind"])


def _note_service(db=Depends(get_db)) -> NoteService:
    """Servicio canónico de Notes: única fuente de verdad del contenido."""
    return NoteService(
        note_repo=NoteRepository(db),
        link_repo=NoteLinkRepository(db),
        tag_repo=TagRepository(db),
        project_repo=ProjectRepository(db),
        task_repo=TaskRepository(db),
        db=db,
    )


def _mind_service(
    db=Depends(get_db), note_service: NoteService = Depends(_note_service)
) -> MindService:
    service = MindService(
        space_repo=MindSpaceRepository(db),
        canvas_repo=MindCanvasRepository(db),
        node_repo=MindNodeRepository(db),
        edge_repo=MindEdgeRepository(db),
        note_service=note_service,
        db=db,
    )
    # Bootstrap idempotente: toda petición de Mind garantiza el Inbox único.
    service.ensure_inbox()
    return service


def _build_space_out(space, canvas_count: int) -> MindSpaceOut:
    """Construye la respuesta de un Space con su conteo de Canvases."""
    out = MindSpaceOut.model_validate(space)
    out.canvas_count = canvas_count
    return out


def _space_out(service: MindService, space) -> MindSpaceOut:
    """Respuesta de un Space individual con su conteo real de Canvases."""
    return _build_space_out(space, service.canvas_count(space.id))


# --- Spaces ---------------------------------------------------------------


@router.get("/spaces", response_model=list[MindSpaceOut])
def list_spaces(
    include_archived: bool = False,
    service: MindService = Depends(_mind_service),
):
    """Lista los Spaces (Inbox incluido) con su conteo de Canvases."""
    return [
        _build_space_out(space, count)
        for space, count in service.list_spaces(include_archived=include_archived)
    ]


@router.post("/spaces", response_model=MindSpaceOut, status_code=status.HTTP_201_CREATED)
def create_space(space_in: MindSpaceCreate, service: MindService = Depends(_mind_service)):
    """Crea un Space con nombre obligatorio y descripción opcional."""
    return _space_out(service, service.create_space(space_in))


@router.get("/spaces/{space_id}", response_model=MindSpaceOut)
def get_space(space_id: str, service: MindService = Depends(_mind_service)):
    """Obtiene un Space por su ID."""
    return _space_out(service, service.get_space(space_id))


@router.patch("/spaces/{space_id}", response_model=MindSpaceOut)
def update_space(
    space_id: str,
    space_in: MindSpaceUpdate,
    service: MindService = Depends(_mind_service),
):
    """Renombra un Space o edita su descripción (no aplica al Inbox)."""
    return _space_out(service, service.update_space(space_id, space_in))


@router.post("/spaces/{space_id}/archive", response_model=MindSpaceOut)
def archive_space(space_id: str, service: MindService = Depends(_mind_service)):
    """Archiva un Space sin eliminar Canvases ni contenido."""
    return _space_out(service, service.archive_space(space_id))


@router.post("/spaces/{space_id}/restore", response_model=MindSpaceOut)
def restore_space(space_id: str, service: MindService = Depends(_mind_service)):
    """Restaura un Space archivado."""
    return _space_out(service, service.restore_space(space_id))


# --- Canvases -------------------------------------------------------------


@router.get(
    "/spaces/{space_id}/canvases", response_model=list[MindCanvasOut]
)
def list_canvases(
    space_id: str,
    include_archived: bool = False,
    service: MindService = Depends(_mind_service),
):
    """Lista los Canvases de un Space."""
    return service.list_canvases(space_id, include_archived=include_archived)


@router.post(
    "/spaces/{space_id}/canvases",
    response_model=MindCanvasOut,
    status_code=status.HTTP_201_CREATED,
)
def create_canvas(
    space_id: str,
    canvas_in: MindCanvasCreate,
    service: MindService = Depends(_mind_service),
):
    """Crea un Canvas dentro de un Space."""
    return service.create_canvas(space_id, canvas_in)


@router.get("/canvases/{canvas_id}", response_model=MindCanvasOut)
def get_canvas(canvas_id: str, service: MindService = Depends(_mind_service)):
    """Obtiene los metadatos de un Canvas."""
    return service.get_canvas(canvas_id)


@router.patch("/canvases/{canvas_id}", response_model=MindCanvasOut)
def update_canvas(
    canvas_id: str,
    canvas_in: MindCanvasUpdate,
    service: MindService = Depends(_mind_service),
):
    """Renombra un Canvas o edita su descripción."""
    return service.update_canvas(canvas_id, canvas_in)


@router.post("/canvases/{canvas_id}/archive", response_model=MindCanvasOut)
def archive_canvas(canvas_id: str, service: MindService = Depends(_mind_service)):
    """Archiva un Canvas conservando sus Cards."""
    return service.archive_canvas(canvas_id)


@router.post("/canvases/{canvas_id}/restore", response_model=MindCanvasOut)
def restore_canvas(canvas_id: str, service: MindService = Depends(_mind_service)):
    """Restaura un Canvas archivado."""
    return service.restore_canvas(canvas_id)


# --- Cards (nodos visuales) ----------------------------------------------


@router.get("/canvases/{canvas_id}/nodes", response_model=list[MindNodeOut])
def list_nodes(canvas_id: str, service: MindService = Depends(_mind_service)):
    """Lista las Cards del Canvas con su contenido canónico y posición."""
    return service.list_nodes(canvas_id)


@router.post(
    "/canvases/{canvas_id}/cards",
    response_model=MindNodeOut,
    status_code=status.HTTP_201_CREATED,
)
def create_card(
    canvas_id: str,
    card_in: MindCardCreate,
    service: MindService = Depends(_mind_service),
):
    """Crea una Card de texto: Note canónica + representación visual."""
    return service.create_card(canvas_id, card_in)


@router.post(
    "/canvases/{canvas_id}/nodes",
    response_model=MindNodeOut,
    status_code=status.HTTP_201_CREATED,
)
def attach_note(
    canvas_id: str,
    attach_in: MindNodeAttach,
    service: MindService = Depends(_mind_service),
):
    """Representa una Note existente sobre el Canvas (sin duplicar contenido)."""
    return service.attach_note(canvas_id, attach_in)


@router.patch(
    "/canvases/{canvas_id}/nodes/{node_id}", response_model=MindNodeOut
)
def update_node(
    canvas_id: str,
    node_id: str,
    node_in: MindNodeUpdate,
    service: MindService = Depends(_mind_service),
):
    """Guarda posición, tamaño u orden visual tras terminar la interacción."""
    return service.update_node(canvas_id, node_id, node_in)


@router.delete(
    "/canvases/{canvas_id}/nodes/{node_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_node(
    canvas_id: str,
    node_id: str,
    service: MindService = Depends(_mind_service),
):
    """Quita la Card del Canvas; la Note canónica no se elimina."""
    service.remove_node(canvas_id, node_id)


# --- Edges (conexiones visuales) -----------------------------------------


@router.get(
    "/canvases/{canvas_id}/edges", response_model=list[MindEdgeOut]
)
def list_edges(canvas_id: str, service: MindService = Depends(_mind_service)):
    """Lista las conexiones del Canvas."""
    return service.list_edges(canvas_id)


@router.post(
    "/canvases/{canvas_id}/edges",
    response_model=MindEdgeOut,
    status_code=status.HTTP_201_CREATED,
)
def create_edge(
    canvas_id: str,
    edge_in: MindEdgeCreate,
    service: MindService = Depends(_mind_service),
):
    """Crea una conexión visual entre dos Cards del mismo Canvas."""
    return service.create_edge(canvas_id, edge_in)


@router.delete(
    "/canvases/{canvas_id}/edges/{edge_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_edge(
    canvas_id: str,
    edge_id: str,
    service: MindService = Depends(_mind_service),
):
    """Elimina una conexión visual."""
    service.remove_edge(canvas_id, edge_id)


# --- Inbox ----------------------------------------------------------------


@router.get("/inbox", response_model=MindInboxOut)
def get_inbox(service: MindService = Depends(_mind_service)):
    """Devuelve el Inbox único con sus capturas."""
    inbox, captures = service.get_inbox()
    return MindInboxOut(
        space=_build_space_out(inbox, 0),
        captures=captures,
    )


@router.post(
    "/inbox/captures",
    response_model=NoteOut,
    status_code=status.HTTP_201_CREATED,
)
def create_capture(
    capture_in: MindCaptureCreate,
    service: MindService = Depends(_mind_service),
):
    """Captura rápida: crea una Note canónica y la asocia al Inbox."""
    return service.create_capture(capture_in)




# --- Historial (undo/redo) ----------------------------------------------

@router.get('/canvases/{canvas_id}/history', response_model=MindHistoryOut)
def get_canvas_history(
    canvas_id: str,
    service: MindService = Depends(_mind_service),
):
    """Obtiene el estado del historial: can_undo, can_redo, accion actual."""
    return service.get_history(canvas_id)


@router.post('/canvases/{canvas_id}/history/undo', response_model=MindHistoryOut)
def undo_history(
    canvas_id: str,
    payload: MindHistoryTransition,
    service: MindService = Depends(_mind_service),
):
    """Deshace la ultima accion (undo)."""
    return service.undo(canvas_id, payload.expected_action_id, payload.idempotency_key)


@router.post('/canvases/{canvas_id}/history/redo', response_model=MindHistoryOut)
def redo_history(
    canvas_id: str,
    payload: MindHistoryTransition,
    service: MindService = Depends(_mind_service),
):
    """Rehace la ultima accion deshecha (redo)."""
    return service.redo(canvas_id, payload.expected_action_id, payload.idempotency_key)

# --- Delete impact --------------------------------------------------------


@router.get("/notes/{note_id}/delete-impact")
def get_delete_impact(
    note_id: str,
    service: MindService = Depends(_mind_service),
):
    """Informa el impacto de eliminar una Note antes de confirmar."""
    return service.get_delete_impact(note_id)
