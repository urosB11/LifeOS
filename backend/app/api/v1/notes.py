"""Rutas API de Notas."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.session import get_db
from app.modules.notes.repository import (
    NoteLinkRepository,
    NoteRepository,
    TagRepository,
)
from app.modules.notes.schemas import (
    LinkRequest,
    NoteCreate,
    NoteOut,
    NoteUpdate,
    TagCreate,
    TagOut,
)
from app.modules.notes.service import NoteService, TagService
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository

router = APIRouter(prefix="/notes", tags=["notes"])


def _note_service(db = Depends(get_db)) -> NoteService:
    return NoteService(
        note_repo=NoteRepository(db),
        link_repo=NoteLinkRepository(db),
        tag_repo=TagRepository(db),
        project_repo=ProjectRepository(db),
        task_repo=TaskRepository(db),
        db=db,
    )


def _tag_service(db = Depends(get_db)) -> TagService:
    return TagService(tag_repo=TagRepository(db), db=db)


# --- Etiquetas (rutas estáticas primero, para evitar conflicto con /{note_id}) ---

@router.post("/tags", response_model=TagOut, status_code=status.HTTP_201_CREATED)
def create_tag(tag_in: TagCreate, service: TagService = Depends(_tag_service)):
    """Crea o reutiliza una etiqueta (evita duplicados por normalización)."""
    try:
        return service.create(tag_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/tags", response_model=list[TagOut])
def list_tags(service: TagService = Depends(_tag_service)):
    """Lista todas las etiquetas."""
    return service.list()


@router.get("/tags/{tag_id}", response_model=TagOut)
def get_tag(tag_id: str, service: TagService = Depends(_tag_service)):
    """Obtiene una etiqueta por su ID."""
    tag = service.get(tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    return tag


@router.get("/tags/{tag_id}/notes", response_model=list[NoteOut])
def get_tag_notes(tag_id: str, service: NoteService = Depends(_note_service)):
    """Consulta las notas vinculadas a una etiqueta."""
    from app.modules.notes.repository import TagRepository

    tag_repo = TagRepository(service.db)
    tag = tag_repo.get(tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Etiqueta no encontrada")
    notes = service.get_notes_for_tag(tag_id)
    return notes


# --- Notas ---

@router.post("", response_model=NoteOut, status_code=status.HTTP_201_CREATED)
def create_note(note_in: NoteCreate, service: NoteService = Depends(_note_service)):
    """Crea una nueva nota."""
    try:
        return service.create(note_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[NoteOut])
def list_notes(
    search: str | None = None,
    tag: str | None = None,
    service: NoteService = Depends(_note_service),
):
    """Lista notas con búsqueda simple y filtro opcional por etiqueta."""
    return service.list(search=search, tag_id=tag)


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: str, service: NoteService = Depends(_note_service)):
    """Obtiene una nota con sus vínculos."""
    note = service.get(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return note


@router.patch("/{note_id}", response_model=NoteOut)
def update_note(
    note_id: str,
    note_in: NoteUpdate,
    service: NoteService = Depends(_note_service),
):
    """Actualiza una nota existente."""
    try:
        note = service.update(note_id, note_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if note is None:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(note_id: str, service: NoteService = Depends(_note_service)):
    """Elimina una nota y sus vínculos (no elimina proyectos, tareas ni etiquetas)."""
    success = service.delete(note_id)
    if not success:
        raise HTTPException(status_code=404, detail="Nota no encontrada")


# --- Vínculos nota-proyecto ---

@router.get("/{note_id}/projects", response_model=list)
def get_note_projects(note_id: str, service: NoteService = Depends(_note_service)):
    """Consulta los proyectos vinculados a una nota."""
    note = service.get(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    projects = service.get_projects(note_id)
    return [{"id": p.id, "name": p.name, "status": p.status} for p in projects]


@router.post("/{note_id}/projects", status_code=status.HTTP_204_NO_CONTENT)
def add_note_project(
    note_id: str,
    link: LinkRequest,
    service: NoteService = Depends(_note_service),
):
    """Vincula una nota a un proyecto."""
    if not service.link_project(note_id, link.id):
        raise HTTPException(status_code=404, detail="Nota o proyecto no encontrado")


@router.delete("/{note_id}/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_note_project(
    note_id: str,
    project_id: str,
    service: NoteService = Depends(_note_service),
):
    """Quita el vínculo entre una nota y un proyecto."""
    if not service.unlink_project(note_id, project_id):
        raise HTTPException(status_code=404, detail="Vínculo no encontrado")


# --- Vínculos nota-tarea ---

@router.get("/{note_id}/tasks", response_model=list)
def get_note_tasks(note_id: str, service: NoteService = Depends(_note_service)):
    """Consulta las tareas vinculadas a una nota."""
    note = service.get(note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="Nota no encontrada")
    tasks = service.get_tasks(note_id)
    return [
        {"id": t.id, "title": t.title, "status": t.status} for t in tasks
    ]


@router.post("/{note_id}/tasks", status_code=status.HTTP_204_NO_CONTENT)
def add_note_task(
    note_id: str,
    link: LinkRequest,
    service: NoteService = Depends(_note_service),
):
    """Vincula una nota a una tarea."""
    if not service.link_task(note_id, link.id):
        raise HTTPException(status_code=404, detail="Nota o tarea no encontrada")


@router.delete("/{note_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_note_task(
    note_id: str,
    task_id: str,
    service: NoteService = Depends(_note_service),
):
    """Quita el vínculo entre una nota y una tarea."""
    if not service.unlink_task(note_id, task_id):
        raise HTTPException(status_code=404, detail="Vínculo no encontrado")


# --- Vínculos nota-etiqueta ---

@router.post("/{note_id}/tags", status_code=status.HTTP_204_NO_CONTENT)
def add_note_tag(
    note_id: str,
    link: LinkRequest,
    service: NoteService = Depends(_note_service),
):
    """Asigna una etiqueta a una nota."""
    if not service.link_tag(note_id, link.id):
        raise HTTPException(status_code=404, detail="Nota o etiqueta no encontrada")


@router.delete("/{note_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_note_tag(
    note_id: str,
    tag_id: str,
    service: NoteService = Depends(_note_service),
):
    """Quita una etiqueta de una nota."""
    if not service.unlink_tag(note_id, tag_id):
        raise HTTPException(status_code=404, detail="Vínculo no encontrado")