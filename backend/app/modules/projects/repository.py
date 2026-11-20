"""Repositorio de Proyectos."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.projects.models import Project
from app.modules.projects.schemas import ProjectCreate, ProjectUpdate


class ProjectRepository:
    """Acceso a datos de la entidad Project."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, project_id: str) -> Project | None:
        return self.db.get(Project, project_id)

    def get_with_tasks(self, project_id: str) -> Project | None:
        stmt = (
            select(Project)
            .where(Project.id == project_id)
            .options(selectinload(Project.tasks))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list(
        self,
        status: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Project]:
        stmt = select(Project)
        if status is not None:
            stmt = stmt.where(Project.status == status)
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count_by_status(self, status: str) -> int:
        stmt = select(func.count(Project.id)).where(Project.status == status)
        return self.db.execute(stmt).scalar_one()

    def count_tasks_by_project(self, project_id: str) -> int:
        from app.modules.tasks.models import Task

        stmt = select(func.count(Task.id)).where(Task.project_id == project_id)
        return self.db.execute(stmt).scalar_one()

    def get_task_metrics(self, project_ids: list[str]) -> dict[str, dict]:
        """Calcula métricas de tareas por proyecto en una sola consulta.

        Métricas (DATABASE.md §8, REQUIREMENTS.md FR-AN-03/04):
        - task_count: total de tareas del proyecto.
        - completed_count: tareas con status='completed'.
        - overdue_count: tareas pending con due_date anterior a hoy (local).
        - next_due_date: menor due_date entre tareas pending con due_date >= hoy.
        """
        from app.core.clock import local_today
        from app.modules.tasks.models import Task

        if not project_ids:
            return {}

        today = local_today(self.db).isoformat()
        stmt = select(Task).where(Task.project_id.in_(project_ids))
        tasks = list(self.db.execute(stmt).scalars().all())

        metrics: dict[str, dict] = {
            pid: {
                "task_count": 0,
                "completed_count": 0,
                "overdue_count": 0,
                "next_due_date": None,
            }
            for pid in project_ids
        }

        for task in tasks:
            pid = task.project_id
            if pid not in metrics:
                continue
            metrics[pid]["task_count"] += 1
            if task.status == "completed":
                metrics[pid]["completed_count"] += 1
            elif task.status == "pending" and task.due_date:
                if task.due_date < today:
                    metrics[pid]["overdue_count"] += 1
                elif (
                    metrics[pid]["next_due_date"] is None
                    or task.due_date < metrics[pid]["next_due_date"]
                ):
                    metrics[pid]["next_due_date"] = task.due_date

        return metrics

    def create(self, project_in: ProjectCreate) -> Project:
        db_obj = Project(
            name=project_in.name,
            description=project_in.description,
            status=project_in.status,
        )
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: Project, project_in: ProjectUpdate) -> Project:
        data = project_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(db_obj, field, value)
        db_obj.updated_at = __import__("app.core.utils", fromlist=["utc_now"]).utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: Project) -> None:
        self.db.delete(db_obj)
        self.db.flush()

    def complete(self, db_obj: Project) -> Project:
        from app.core.utils import utc_now

        db_obj.status = "completed"
        db_obj.completed_at = utc_now()
        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def reopen(self, db_obj: Project) -> Project:
        from app.core.utils import utc_now

        db_obj.status = "active"
        db_obj.completed_at = None
        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def archive(self, db_obj: Project) -> Project:
        from app.core.utils import utc_now

        db_obj.status = "archived"
        db_obj.archived_at = utc_now()
        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def restore(self, db_obj: Project) -> Project:
        from app.core.utils import utc_now

        db_obj.status = "active"
        db_obj.archived_at = None
        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj