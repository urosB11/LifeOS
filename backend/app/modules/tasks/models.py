"""Modelo de datos de Tareas."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import new_uuid, utc_now
from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.projects.models import Project


class Task(Base):
    """Tarea con estado, prioridad opcional y vencimiento opcional.

    Reglas de negocio (DATABASE.md sección 5.2):
    - id es UUIDv4 como texto.
    - project_id es FK nullable a projects.id con ON DELETE RESTRICT.
    - title es obligatorio y no vacío.
    - status default 'pending'; valores: pending, completed.
    - priority nullable: low, normal, high.
    - due_date nullable: YYYY-MM-DD de calendario local.
    - completed_at se establece al completar y se limpia al reabrir.
    """

    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    project_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("projects.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    priority: Mapped[str | None] = mapped_column(String(10), nullable=True)
    due_date: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    created_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )
    completed_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    project: Mapped[Project | None] = relationship(back_populates="tasks")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Task(id={self.id}, title={self.title!r}, status={self.status})>"