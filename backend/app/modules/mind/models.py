"""Modelos de datos de Mind: Spaces, Canvases, membresías, nodos y edges (MIND-002/003).

Límites de esta entrega (SPEC MIND-002 §3, MIND-003 §2):
- `mind_canvas_edges` para conexiones visuales no dirigidas entre Cards.
- El contenido canónico sigue siendo `notes`; estas tablas guardan contextos
  y representaciones visuales, nunca copias del texto.
"""

from __future__ import annotations

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    ForeignKeyConstraint,
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

    El Canvas tiene identidad y metadatos propios; archivarlo conserva sus
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


class MindCanvasEdge(Base):
    """Conexión visual no dirigida entre dos Cards del mismo Canvas (MIND-003).

    - `source_node_id` y `target_node_id` referencian `mind_canvas_nodes.id`.
    - La pareja (source, target) se almacena normalizada (menor ID primero)
      para evitar duplicados A→B y B→A.
    - `source_anchor`/`target_anchor` ∈ [0..7] indican el punto de anclaje
      en el perímetro de cada Card (0=centro sup, 1=esq sup der, ...).
    - FK simple a mind_canvas_nodes.id + CHECK para validar mismo canvas.
    - ON DELETE CASCADE: al borrar una Card, sus conexiones se eliminan.
    """

    __tablename__ = "mind_canvas_edges"

    __table_args__ = (
        ForeignKeyConstraint(
            ["source_node_id"],
            ["mind_canvas_nodes.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["target_node_id"],
            ["mind_canvas_nodes.id"],
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["canvas_id"],
            ["mind_canvases.id"],
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "canvas_id",
            "source_node_id",
            "target_node_id",
            name="uq_mind_canvas_edges_canvas_source_target",
        ),
        CheckConstraint(
            "source_node_id < target_node_id",
            name="ck_mind_canvas_edges_source_lt_target",
        ),
        CheckConstraint(
            "source_anchor BETWEEN 0 AND 7",
            name="ck_mind_canvas_edges_source_anchor",
        ),
        CheckConstraint(
            "target_anchor BETWEEN 0 AND 7",
            name="ck_mind_canvas_edges_target_anchor",
        ),
        Index(
            "ix_mind_canvas_edges_canvas_source",
            "canvas_id",
            "source_node_id",
        ),
        Index(
            "ix_mind_canvas_edges_canvas_target",
            "canvas_id",
            "target_node_id",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    canvas_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("mind_canvases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    source_node_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    target_node_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    source_anchor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    target_anchor: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)
    updated_at: Mapped[str] = mapped_column(
        String(32), nullable=False, default=utc_now, onupdate=utc_now
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MindCanvasEdge(id={self.id}, canvas={self.canvas_id}, {self.source_node_id}→{self.target_node_id})>"


class MindCanvasHistory(Base):
    """Historial espacial reversible y acotado por Canvas (MIND-003).

    Almacena snapshots de operaciones para soportar undo/redo.
    - action_type: tipo de operacion (create_node, update_node, delete_node,
      create_edge, delete_edge, reorder, batch).
    - snapshot_json: estado del Canvas antes de la accion (nodos, edges, z-index).
    - inverse_json: operacion inversa para redo (cuando corresponde).
    - request_key: clave idempotente de la solicitud original.
    - Acotado: se purgan entradas antiguas por Canvas (p. ej., 100 ultimas).
    """

    __tablename__ = "mind_canvas_history"

    __table_args__ = (
        ForeignKeyConstraint(
            ["canvas_id"],
            ["mind_canvases.id"],
            ondelete="CASCADE",
        ),
        Index(
            "ix_mind_canvas_history_canvas_created",
            "canvas_id",
            "created_at",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    canvas_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("mind_canvases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(String(30), nullable=False)
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    inverse_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    request_key: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default=utc_now)

    def __repr__(self) -> str:  # pragma: no cover
        return f"<MindCanvasHistory(id={self.id}, canvas={self.canvas_id}, action={self.action_type})>"

__all__ = [
    "MindSpace",
    "MindCanvas",
    "MindSpaceNote",
    "MindCanvasNode",
    "MindCanvasEdge",
    "MindCanvasHistory",
]
