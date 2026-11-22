"""Modelos de datos de Mind: Spaces, Canvases, membresías y nodos (MIND-002).

Límites de esta entrega (SPEC MIND-002 §3):
- No existen `mind_canvas_edges`, relaciones semánticas ni documentos por
  bloques: quedan para MIND-003 y MIND-004.
- El contenido canónico sigue siendo `notes`; estas tablas guardan contextos
  y representaciones visuales, nunca copias del texto.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import new_uuid, utc_now
from app.db.base import Base
from app.modules.notes.models import Note


class MindSpace(Base):
    """Contexto flexible de trabajo (SPEC MIND-002 §2.2 y §2.3).

    Reglas:
    - `is_inbox` marca el Inbox único de la instalación; un índice único
      parcial garantiza a lo sumo un Inbox a nivel de base de datos.
    - `status`: `active` o `archived`. Archivar no elimina Canvases ni
      contenido canónico.
    - El Inbox no se renombra, archiva ni elimina desde la UI (servicio).
    """

    __tablename__ = "mind_spaces"

    __table_args__ = (
        Index(
            "uq_mind_spaces_is_inbox",
            "is_inbox",
            unique=True,
            sqlite_where=text("is_inbox = 1"),
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_inbox: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    archived_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MindSpace(id={self.id}, name={self.name!r}, inbox={self.is_inbox})>"


class MindCanvas(Base):
    """Supericie visual libre dentro de un Space (SPEC MIND-002 §2.4).

    El Canvas tiene identidad y metadados propios; archivarlo conserva sus
    nodos y el contenido de las Notes referenciadas.
    """

    __tablename__ = "mind_canvases"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    space_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("mind_spaces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", index=True
    )
    archived_at: Mapped[str | None] = mapped_column(String(32), nullable=True)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MindCanvas(id={self.id}, title={self.title!r})>"


class MindSpaceNote(Base):
    """Membresía de una Note en un Space (Inbox incluido).

    Permite consultar y editar una captura con el servicio/API canónico de
    Notes sin duplicar contenido. Eliminar la Note elimina la membresía
    mediante `ON DELETE CASCADE`.
    """

    __tablename__ = "mind_space_notes"

    space_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("mind_spaces.id", ondelete="CASCADE"),
        primary_key=True,
    )
    note_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notes.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)


class MindCanvasNode(Base):
    """Instancia visual de una Note sobre un Canvas (SPEC MIND-002 §2.5).

    - `x`/`y` son coordenadas del mundo, independientes del viewport y zoom.
    - `width`/`height` son el tamaño inicial; NULL usa el tamaño por defecto.
    - Quitar el nodo no elimina la Note; la Note se elimina junto con sus
      referencias visuales (`ON DELETE CASCADE`).
    - UNIQUE(canvas_id, note_id): una representación por Note en cada Canvas;
      la misma Note puede vivir en varios Canvases.
    """

    __tablename__ = "mind_canvas_nodes"

    __table_args__ = (
        UniqueConstraint(
            "canvas_id",
            "note_id",
            name="uq_mind_canvas_nodes_canvas_id_note_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    canvas_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("mind_canvases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    note_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    x: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    y: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    width: Mapped[float | None] = mapped_column(Float, nullable=True)
    height: Mapped[float | None] = mapped_column(Float, nullable=True)
    z_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )

    note: Mapped[Note] = relationship(Note, lazy="selectin")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MindCanvasNode(id={self.id}, canvas_id={self.canvas_id})>"


__all__ = ["MindSpace", "MindCanvas", "MindSpaceNote", "MindCanvasNode"]
