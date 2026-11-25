"""Repositorios de Mind: Spaces, Canvases, membresías, nodos y edges (MIND-002/003)."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.modules.mind.models import (
    MindCanvas,
    MindCanvasEdge,
    MindCanvasNode,
    MindSpace,
    MindSpaceNote,
)
from app.modules.mind.schemas import (
    MindCanvasCreate,
    MindCanvasUpdate,
    MindNodeUpdate,
    MindSpaceCreate,
    MindSpaceUpdate,
)
from app.modules.notes.models import Note


class MindSpaceRepository:
    """Acceso a datos de Spaces y membresías Note↔Space."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, space_id: str) -> MindSpace | None:
        return self.db.get(MindSpace, space_id)

    def get_inbox(self) -> MindSpace | None:
        stmt = select(MindSpace).where(MindSpace.is_inbox.is_(True))
        return self.db.execute(stmt).scalar_one_or_none()

    def list(self, include_archived: bool = False) -> list[MindSpace]:
        stmt = select(MindSpace)
        if not include_archived:
            stmt = stmt.where(MindSpace.status == "active")
        # Inbox primero y luego orden alfabético estable.
        stmt = stmt.order_by(MindSpace.is_inbox.desc(), MindSpace.name)
        return list(self.db.execute(stmt).scalars().all())

    def canvas_counts(self) -> dict[str, int]:
        """Conteo de Canvases por Space (incluye archivados: siguen existiendo)."""
        stmt = select(MindCanvas.space_id, func.count(MindCanvas.id)).group_by(
            MindCanvas.space_id
        )
        return dict(self.db.execute(stmt).all())

    def create(self, space_in: MindSpaceCreate, *, is_inbox: bool = False) -> MindSpace:
        space = MindSpace(
            name=space_in.name,
            description=space_in.description,
            is_inbox=is_inbox,
        )
        self.db.add(space)
        self.db.flush()
        self.db.refresh(space)
        return space

    def update(self, space: MindSpace, space_in: MindSpaceUpdate) -> MindSpace:
        data = space_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(space, field, value)
        self.db.add(space)
        self.db.flush()
        self.db.refresh(space)
        return space

    def archive(self, space: MindSpace) -> MindSpace:
        from app.core.utils import utc_now

        space.status = "archived"
        space.archived_at = utc_now()
        self.db.add(space)
        self.db.flush()
        self.db.refresh(space)
        return space

    def restore(self, space: MindSpace) -> MindSpace:
        space.status = "active"
        space.archived_at = None
        self.db.add(space)
        self.db.flush()
        self.db.refresh(space)
        return space

    # --- membresías Note↔Space ---
    def add_membership(self, space_id: str, note_id: str) -> MindSpaceNote | None:
        """Añade una Note al Space de forma idempotente."""
        existing = self.get_membership(space_id, note_id)
        if existing is not None:
            return existing
        link = MindSpaceNote(space_id=space_id, note_id=note_id)
        self.db.add(link)
        self.db.flush()
        return link

    def get_membership(self, space_id: str, note_id: str) -> MindSpaceNote | None:
        stmt = select(MindSpaceNote).where(
            MindSpaceNote.space_id == space_id,
            MindSpaceNote.note_id == note_id,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def list_captures(self, space_id: str, limit: int = 200) -> list[Note]:
        """Notes miembras del Space, más recientes primero."""
        stmt = (
            select(Note)
            .join(MindSpaceNote, MindSpaceNote.note_id == Note.id)
            .where(MindSpaceNote.space_id == space_id)
            .order_by(Note.updated_at.desc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())


class MindCanvasRepository:
    """Acceso a datos de Canvases."""

    def __init__(self, db: Session):
        self.db = db

    def get(self, canvas_id: str) -> MindCanvas | None:
        return self.db.get(MindCanvas, canvas_id)

    def list_for_space(
        self, space_id: str, include_archived: bool = False
    ) -> list[MindCanvas]:
        stmt = select(MindCanvas).where(MindCanvas.space_id == space_id)
        if not include_archived:
            stmt = stmt.where(MindCanvas.status == "active")
        stmt = stmt.order_by(MindCanvas.updated_at.desc(), MindCanvas.created_at.desc())
        return list(self.db.execute(stmt).scalars().all())

    def create(self, space_id: str, canvas_in: MindCanvasCreate) -> MindCanvas:
        canvas = MindCanvas(
            space_id=space_id,
            title=canvas_in.title,
            description=canvas_in.description,
        )
        self.db.add(canvas)
        self.db.flush()
        self.db.refresh(canvas)
        return canvas

    def update(self, canvas: MindCanvas, canvas_in: MindCanvasUpdate) -> MindCanvas:
        data = canvas_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(canvas, field, value)
        self.db.add(canvas)
        self.db.flush()
        self.db.refresh(canvas)
        return canvas

    def archive(self, canvas: MindCanvas) -> MindCanvas:
        from app.core.utils import utc_now

        canvas.status = "archived"
        canvas.archived_at = utc_now()
        self.db.add(canvas)
        self.db.flush()
        self.db.refresh(canvas)
        return canvas

    def restore(self, canvas: MindCanvas) -> MindCanvas:
        canvas.status = "active"
        canvas.archived_at = None
        self.db.add(canvas)
        self.db.flush()
        self.db.refresh(canvas)
        return canvas


class MindNodeRepository:
    """Acceso a datos de nodos visuales (Cards) sobre un Canvas."""

    def __init__(self, db: Session):
        self.db = db

    def list_for_canvas(self, canvas_id: str) -> list[MindCanvasNode]:
        stmt = (
            select(MindCanvasNode)
            .where(MindCanvasNode.canvas_id == canvas_id)
            .options(selectinload(MindCanvasNode.note))
            .order_by(MindCanvasNode.z_index, MindCanvasNode.created_at)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get(self, node_id: str) -> MindCanvasNode | None:
        stmt = (
            select(MindCanvasNode)
            .where(MindCanvasNode.id == node_id)
            .options(selectinload(MindCanvasNode.note))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_by_canvas_and_note(
        self, canvas_id: str, note_id: str
    ) -> MindCanvasNode | None:
        stmt = (
            select(MindCanvasNode)
            .where(
                MindCanvasNode.canvas_id == canvas_id,
                MindCanvasNode.note_id == note_id,
            )
            .options(selectinload(MindCanvasNode.note))
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(
        self,
        canvas_id: str,
        note_id: str,
        *,
        x: float,
        y: float,
        width: float | None,
        height: float | None,
        z_index: int | None,
    ) -> MindCanvasNode:
        node = MindCanvasNode(
            canvas_id=canvas_id,
            note_id=note_id,
            x=x,
            y=y,
            width=width,
            height=height,
            z_index=0 if z_index is None else z_index,
        )
        self.db.add(node)
        self.db.flush()
        return self.get(node.id)

    def update(self, node: MindCanvasNode, node_in: MindNodeUpdate) -> MindCanvasNode:
        data = node_in.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(node, field, value)
        self.db.add(node)
        self.db.flush()
        return self.get(node.id)

    def delete(self, node: MindCanvasNode) -> None:
        self.db.delete(node)
        self.db.flush()


class MindEdgeRepository:
    """Acceso a datos de conexiones visuales (edges) sobre un Canvas."""

    def __init__(self, db: Session):
        self.db = db

    def list_for_canvas(self, canvas_id: str) -> list[MindCanvasEdge]:
        stmt = (
            select(MindCanvasEdge)
            .where(MindCanvasEdge.canvas_id == canvas_id)
            .order_by(MindCanvasEdge.created_at)
        )
        return list(self.db.execute(stmt).scalars().all())

    def get(self, edge_id: str) -> MindCanvasEdge | None:
        stmt = select(MindCanvasEdge).where(MindCanvasEdge.id == edge_id)
        return self.db.execute(stmt).scalar_one_or_none()

    def find_by_canvas_and_nodes(
        self, canvas_id: str, source_id: str, target_id: str
    ) -> MindCanvasEdge | None:
        # La pareja se almacena normalizada (source < target)
        a, b = sorted([source_id, target_id])
        stmt = select(MindCanvasEdge).where(
            MindCanvasEdge.canvas_id == canvas_id,
            MindCanvasEdge.source_node_id == a,
            MindCanvasEdge.target_node_id == b,
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def create(
        self,
        canvas_id: str,
        source_id: str,
        target_id: str,
        source_anchor: int = 0,
        target_anchor: int = 0,
    ) -> MindCanvasEdge:
        a, b = sorted([source_id, target_id])
        edge = MindCanvasEdge(
            canvas_id=canvas_id,
            source_node_id=a,
            target_node_id=b,
            source_anchor=source_anchor if source_id == a else target_anchor,
            target_anchor=target_anchor if target_id == b else source_anchor,
        )
        self.db.add(edge)
        self.db.flush()
        return self.get(edge.id)

    def delete(self, edge: MindCanvasEdge) -> None:
        self.db.delete(edge)
        self.db.flush()

    def delete_by_node(self, canvas_id: str, node_id: str) -> int:
        """Elimina todas las edges conectadas a un nodo. Devuelve cantidad eliminada."""
        stmt = select(MindCanvasEdge).where(
            MindCanvasEdge.canvas_id == canvas_id,
            (MindCanvasEdge.source_node_id == node_id)
            | (MindCanvasEdge.target_node_id == node_id),
        )
        edges = list(self.db.execute(stmt).scalars().all())
        for edge in edges:
            self.db.delete(edge)
        self.db.flush()
        return len(edges)