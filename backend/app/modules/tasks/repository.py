"""Repositorio de Tareas."""

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from app.modules.tasks.models import Task
from app.modules.tasks.schemas import TaskCreate, TaskUpdate


class TaskRepository:
    """Acceso a datos de la entidad Task."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, task_id: str) -> Task | None:
        return self.db.get(Task, task_id)

    def list(
        self,
        status: str | None = None,
        priority: str | None = None,
        project_id: str | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        stmt = select(Task)
        conditions = []
        if status is not None:
            conditions.append(Task.status == status)
        if priority is not None:
            conditions.append(Task.priority == priority)
        if project_id is not None:
            conditions.append(Task.project_id == project_id)
        if conditions:
            stmt = stmt.where(and_(*conditions))
        stmt = stmt.offset(skip).limit(limit)
        return list(self.db.execute(stmt).scalars().all())

    def count(self, status: str | None = None) -> int:
        stmt = select(func.count(Task.id))
        if status is not None:
            stmt = stmt.where(Task.status == status)
        return self.db.execute(stmt).scalar_one()

    def count_overdue(self) -> int:
        """Tareas pendientes con due_date anterior a la fecha local actual."""
        from datetime import date

        today = date.today().isoformat()
        stmt = select(func.count(Task.id)).where(
            and_(
                Task.status == "pending",
                Task.due_date.is_not(None),
                Task.due_date < today,
            )
        )
        return self.db.execute(stmt).scalar_one()

    def create(self, task_in: TaskCreate) -> Task:
        db_obj = Task(
            title=task_in.title,
            description=task_in.description,
            status=task_in.status,
            priority=task_in.priority,
            due_date=task_in.due_date,
            project_id=task_in.project_id,
        )
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def update(self, db_obj: Task, task_in: TaskUpdate) -> Task:
        data = task_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(db_obj, field, value)
        from app.core.utils import utc_now

        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def delete(self, db_obj: Task) -> None:
        self.db.delete(db_obj)
        self.db.flush()

    def complete(self, db_obj: Task) -> Task:
        from app.core.utils import utc_now

        db_obj.status = "completed"
        db_obj.completed_at = utc_now()
        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj

    def reopen(self, db_obj: Task) -> Task:
        from app.core.utils import utc_now

        db_obj.status = "pending"
        db_obj.completed_at = None
        db_obj.updated_at = utc_now()
        self.db.add(db_obj)
        self.db.flush()
        self.db.refresh(db_obj)
        return db_obj