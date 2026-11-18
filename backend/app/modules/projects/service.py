"""Servicio de Proyectos.

Implementa reglas de negocio y registra eventos de actividad en la misma
transacción que el cambio de dominio (DATABASE.md sección 6).
"""

from app.db.activity import record_event
from app.modules.projects.repository import ProjectRepository
from app.modules.projects.schemas import ProjectCreate, ProjectOut, ProjectUpdate
from app.modules.tasks.repository import TaskRepository


class ProjectService:
    """Casos de uso de proyectos."""

    def __init__(self, project_repo: ProjectRepository, task_repo: TaskRepository, db):
        self.project_repo = project_repo
        self.task_repo = task_repo
        self.db = db

    def create(self, project_in: ProjectCreate) -> ProjectOut:
        project = self.project_repo.create(project_in)
        record_event(
            self.db,
            event_type="project.created",
            entity_type="project",
            entity_id=project.id,
            metadata={"name": project.name, "status": project.status},
        )
        return ProjectOut.model_validate(project)

    def get(self, project_id: str) -> ProjectOut | None:
        project = self.project_repo.get_with_tasks(project_id)
        if project is None:
            return None
        return ProjectOut.model_validate(project)

    def list(self, status: str | None = None) -> list[ProjectOut]:
        projects = self.project_repo.list(status=status)
        return [ProjectOut.model_validate(p) for p in projects]

    def update(self, project_id: str, project_in: ProjectUpdate) -> ProjectOut | None:
        project = self.project_repo.get(project_id)
        if project is None:
            return None
        updated = self.project_repo.update(project, project_in)
        record_event(
            self.db,
            event_type="project.updated",
            entity_type="project",
            entity_id=project_id,
            metadata={"fields": list(project_in.model_dump(exclude_unset=True).keys())},
        )
        return ProjectOut.model_validate(updated)

    def complete(self, project_id: str) -> ProjectOut | None:
        project = self.project_repo.get(project_id)
        if project is None:
            return None
        if project.status == "completed":
            return ProjectOut.model_validate(project)
        updated = self.project_repo.complete(project)
        record_event(
            self.db,
            event_type="project.completed",
            entity_type="project",
            entity_id=project_id,
        )
        return ProjectOut.model_validate(updated)

    def reopen(self, project_id: str) -> ProjectOut | None:
        project = self.project_repo.get(project_id)
        if project is None:
            return None
        if project.status == "active":
            return ProjectOut.model_validate(project)
        updated = self.project_repo.reopen(project)
        record_event(
            self.db,
            event_type="project.reopened",
            entity_type="project",
            entity_id=project_id,
        )
        return ProjectOut.model_validate(updated)

    def archive(self, project_id: str) -> ProjectOut | None:
        project = self.project_repo.get(project_id)
        if project is None:
            return None
        if project.status == "archived":
            return ProjectOut.model_validate(project)
        updated = self.project_repo.archive(project)
        record_event(
            self.db,
            event_type="project.archived",
            entity_type="project",
            entity_id=project_id,
        )
        return ProjectOut.model_validate(updated)

    def restore(self, project_id: str) -> ProjectOut | None:
        project = self.project_repo.get(project_id)
        if project is None:
            return None
        if project.status == "active":
            return ProjectOut.model_validate(project)
        updated = self.project_repo.restore(project)
        record_event(
            self.db,
            event_type="project.restored",
            entity_type="project",
            entity_id=project_id,
        )
        return ProjectOut.model_validate(updated)

    def delete(self, project_id: str) -> bool:
        """Elimina físicamente un proyecto solo si no tiene tareas asociadas.

        Reglas (DATABASE.md sección 6):
        - Borrado restringido si hay tareas.
        - Archivar es la operación preferida.
        """
        project = self.project_repo.get(project_id)
        if project is None:
            return False
        task_count = self.project_repo.count_tasks_by_project(project_id)
        if task_count > 0:
            return False
        self.project_repo.delete(project)
        record_event(
            self.db,
            event_type="project.deleted",
            entity_type="project",
            entity_id=project_id,
        )
        return True