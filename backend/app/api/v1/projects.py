"""Rutas API de Proyectos."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.session import get_db
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.schemas import (
    ProjectCreate,
    ProjectOut,
    ProjectUpdate,
)
from app.modules.projects.service import ProjectService
from app.modules.tasks.repository import TaskRepository

router = APIRouter(prefix="/projects", tags=["projects"])


def _service(db = Depends(get_db)) -> ProjectService:
    return ProjectService(
        project_repo=ProjectRepository(db),
        task_repo=TaskRepository(db),
        db=db,
    )


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(project_in: ProjectCreate, service: ProjectService = Depends(_service)):
    """Crea un nuevo proyecto."""
    return service.create(project_in)


@router.get("", response_model=list[ProjectOut])
def list_projects(status: str | None = None, service: ProjectService = Depends(_service)):
    """Lista proyectos, opcionalmente filtrados por estado."""
    return service.list(status=status)


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: str, service: ProjectService = Depends(_service)):
    """Obtiene un proyecto por su ID."""
    project = service.get(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@router.patch("/{project_id}", response_model=ProjectOut)
def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    service: ProjectService = Depends(_service),
):
    """Actualiza un proyecto existente."""
    project = service.update(project_id, project_in)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@router.post("/{project_id}/complete", response_model=ProjectOut)
def complete_project(project_id: str, service: ProjectService = Depends(_service)):
    """Marca un proyecto como completado."""
    project = service.complete(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@router.post("/{project_id}/reopen", response_model=ProjectOut)
def reopen_project(project_id: str, service: ProjectService = Depends(_service)):
    """Vuelve a abrir un proyecto completado."""
    project = service.reopen(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@router.post("/{project_id}/archive", response_model=ProjectOut)
def archive_project(project_id: str, service: ProjectService = Depends(_service)):
    """Archiva un proyecto."""
    project = service.archive(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@router.post("/{project_id}/restore", response_model=ProjectOut)
def restore_project(project_id: str, service: ProjectService = Depends(_service)):
    """Restaura un proyecto archivado a activo."""
    project = service.restore(project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: str, service: ProjectService = Depends(_service)):
    """Elimina físicamente un proyecto solo si no tiene tareas asociadas."""
    success = service.delete(project_id)
    if not success:
        # Puede ser que no exista o que tenga tareas
        project = service.get(project_id)
        if project is None:
            raise HTTPException(status_code=404, detail="Proyecto no encontrado")
        raise HTTPException(
            status_code=409,
            detail="No se puede eliminar un proyecto que tiene tareas asociadas. Archivalo en su lugar.",
        )