"""Modelo de datos de Proyectos."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import new_uuid, utc_now
from app.db.base import Base

if TYPE_CHECKING:
    from app.modules.tasks.models import Task


class Project(Base):
    """Proyecto con ciclo de vida activo/completado/archivado.

    Reglas de negocio (DATABASE.md sección 5.1):
    - id es UUIDv4 como texto.
    - name es obligatorio y no vacío.
    - status default 'active'; valores permitidos: active, completed, archived.
    - completed_at se establece al completar y se limpia al reabrir.
    - archived_at se establece al archivar y se limpia al restaurar.
    """

    __tablename__ = "projects"

    __table_args__ = (Index("ix_projects_status", "status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    created_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now
    )
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )
    completed_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    archived_at: Mapped[str | None] = mapped_column(String(32), nullable=True)

    tasks: Mapped[list[Task]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Project(id={self.id}, name={self.name!r}, status={self.status})>"