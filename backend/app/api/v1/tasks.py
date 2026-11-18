"""Rutas API de Tareas."""

from fastapi import APIRouter, Depends, HTTPException, status

from app.db.session import get_db
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import TaskCreate, TaskOut, TaskUpdate
from app.modules.tasks.service import TaskService

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _service(db = Depends(get_db)) -> TaskService:
    return TaskService(
        task_repo=TaskRepository(db),
        project_repo=ProjectRepository(db),
        db=db,
    )


@router.post("", response_model=TaskOut, status_code=status.HTTP_201_CREATED)
def create_task(task_in: TaskCreate, service: TaskService = Depends(_service)):
    """Crea una nueva tarea."""
    try:
        return service.create(task_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[TaskOut])
def list_tasks(
    status: str | None = None,
    priority: str | None = None,
    project_id: str | None = None,
    service: TaskService = Depends(_service),
):
    """Lista tareas con filtros opcionales por estado, prioridad y proyecto."""
    return service.list(status=status, priority=priority, project_id=project_id)


@router.get("/{task_id}", response_model=TaskOut)
def get_task(task_id: str, service: TaskService = Depends(_service)):
    """Obtiene una tarea por su ID."""
    task = service.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


@router.patch("/{task_id}", response_model=TaskOut)
def update_task(
    task_id: str,
    task_in: TaskUpdate,
    service: TaskService = Depends(_service),
):
    """Actualiza una tarea existente."""
    try:
        task = service.update(task_id, task_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


@router.post("/{task_id}/complete", response_model=TaskOut)
def complete_task(task_id: str, service: TaskService = Depends(_service)):
    """Marca una tarea como completada."""
    task = service.complete(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


@router.post("/{task_id}/reopen", response_model=TaskOut)
def reopen_task(task_id: str, service: TaskService = Depends(_service)):
    """Vuelve a abrir una tarea completada."""
    task = service.reopen(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: str, service: TaskService = Depends(_service)):
    """Elimina una tarea."""
    success = service.delete(task_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")