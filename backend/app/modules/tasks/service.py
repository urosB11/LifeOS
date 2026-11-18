"""Servicio de Tareas.

Implementa reglas de negocio y registra eventos de actividad en la misma
transacción que el cambio de dominio (DATABASE.md sección 6).
"""

from app.db.activity import record_event
from app.modules.projects.repository import ProjectRepository
from app.modules.tasks.repository import TaskRepository
from app.modules.tasks.schemas import TaskCreate, TaskOut, TaskUpdate


class TaskService:
    """Casos de uso de tareas."""

    def __init__(self, task_repo: TaskRepository, project_repo: ProjectRepository, db):
        self.task_repo = task_repo
        self.project_repo = project_repo
        self.db = db

    def create(self, task_in: TaskCreate) -> TaskOut:
        # Validar que el proyecto exista si se proporciona project_id
        if task_in.project_id is not None:
            project = self.project_repo.get(task_in.project_id)
            if project is None:
                raise ValueError(f"Proyecto no encontrado: {task_in.project_id}")
        task = self.task_repo.create(task_in)
        record_event(
            self.db,
            event_type="task.created",
            entity_type="task",
            entity_id=task.id,
            metadata={
                "title": task.title,
                "status": task.status,
                "project_id": task.project_id,
            },
        )
        return TaskOut.model_validate(task)

    def get(self, task_id: str) -> TaskOut | None:
        task = self.task_repo.get(task_id)
        if task is None:
            return None
        return TaskOut.model_validate(task)

    def list(
        self,
        status: str | None = None,
        priority: str | None = None,
        project_id: str | None = None,
    ) -> list[TaskOut]:
        tasks = self.task_repo.list(
            status=status, priority=priority, project_id=project_id
        )
        return [TaskOut.model_validate(t) for t in tasks]

    def update(self, task_id: str, task_in: TaskUpdate) -> TaskOut | None:
        task = self.task_repo.get(task_id)
        if task is None:
            return None
        if task_in.project_id is not None and task_in.project_id != task.project_id:
            project = self.project_repo.get(task_in.project_id)
            if project is None:
                raise ValueError(f"Proyecto no encontrado: {task_in.project_id}")
        updated = self.task_repo.update(task, task_in)
        record_event(
            self.db,
            event_type="task.updated",
            entity_type="task",
            entity_id=task_id,
            metadata={"fields": list(task_in.model_dump(exclude_unset=True).keys())},
        )
        return TaskOut.model_validate(updated)

    def complete(self, task_id: str) -> TaskOut | None:
        task = self.task_repo.get(task_id)
        if task is None:
            return None
        if task.status == "completed":
            return TaskOut.model_validate(task)
        updated = self.task_repo.complete(task)
        record_event(
            self.db,
            event_type="task.completed",
            entity_type="task",
            entity_id=task_id,
        )
        return TaskOut.model_validate(updated)

    def reopen(self, task_id: str) -> TaskOut | None:
        task = self.task_repo.get(task_id)
        if task is None:
            return None
        if task.status == "pending":
            return TaskOut.model_validate(task)
        updated = self.task_repo.reopen(task)
        record_event(
            self.db,
            event_type="task.reopened",
            entity_type="task",
            entity_id=task_id,
        )
        return TaskOut.model_validate(updated)

    def delete(self, task_id: str) -> bool:
        task = self.task_repo.get(task_id)
        if task is None:
            return False
        self.task_repo.delete(task)
        record_event(
            self.db,
            event_type="task.deleted",
            entity_type="task",
            entity_id=task_id,
        )
        return True