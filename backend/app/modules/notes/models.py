"""Modelos de datos de Notas, vínculos y etiquetas."""

from __future__ import annotations

from sqlalchemy import ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import new_uuid, utc_now
from app.db.base import Base


class Note(Base):
    """Nota de texto independiente o vinculada a proyectos y tareas.

    Reglas (DATABASE.md sección 5.3):
    - Sin FK directa a proyectos o tareas; las relaciones van en tablas de unión.
    - created_at y updated_at obligatorios.
    - contenido es texto plano.
    """

    __tablename__ = "notes"

    __table_args__ = (Index("ix_notes_updated_at", "updated_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )

    project_links: Mapped[list[NoteProjectLink]] = relationship(
        back_populates="note", cascade="all, delete-orphan"
    )
    task_links: Mapped[list[NoteTaskLink]] = relationship(
        back_populates="note", cascade="all, delete-orphan"
    )
    tag_links: Mapped[list[NoteTag]] = relationship(
        back_populates="note", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Note(id={self.id}, title={self.title!r})>"


class NoteProjectLink(Base):
    """Vínculo muchos-a-muchos entre nota y proyecto."""

    __tablename__ = "note_project_links"

    __table_args__ = (Index("ix_note_project_links_project_id", "project_id"),)

    note_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True
    )
    project_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)

    note: Mapped[Note] = relationship(back_populates="project_links")


class NoteTaskLink(Base):
    """Vínculo muchos-a-muchos entre nota y tarea."""

    __tablename__ = "note_task_links"

    __table_args__ = (Index("ix_note_task_links_task_id", "task_id"),)

    note_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True
    )
    task_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)

    note: Mapped[Note] = relationship(back_populates="task_links")


class Tag(Base):
    """Etiqueta reutilizable compartida entre notas.

    Reglas (DATABASE.md sección 5.6):
    - name es el nombre visible obligatorio.
    - normalized_name es UNIQUE (case-insensitive, colapsa espacios).
    - No se permite renombrado ni eliminación desde la UI en el MVP.
    """

    __tablename__ = "tags"

    __table_args__ = (
        UniqueConstraint(
            "normalized_name",
            name="uq_tags_normalized_name",
        ),
        Index("ix_tags_normalized_name", "normalized_name", unique=True),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_name: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)

    note_links: Mapped[list[NoteTag]] = relationship(
        back_populates="tag", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Tag(id={self.id}, name={self.name!r})>"


class NoteTag(Base):
    """Asignación muchos-a-muchos entre nota y etiqueta."""

    __tablename__ = "note_tags"

    __table_args__ = (Index("ix_note_tags_tag_id", "tag_id"),)

    note_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)

    note: Mapped[Note] = relationship(back_populates="tag_links")
    tag: Mapped[Tag] = relationship(back_populates="note_links")