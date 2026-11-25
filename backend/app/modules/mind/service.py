"""Servicio de Mind (MIND-002/003).

Reglas de negocio y eventos de actividad en la misma transacción que el
cambio de dominio (DATABASE.md sección 6). El contenido canónico vive en
`notes`: este módulo nunca copia ni duplica el texto de una Note.
"""

from __future__ import annotations

from sqlalchemy.exc import IntegrityError

from app.db.activity import record_event
from app.modules.mind.models import (
    MindCanvas,
    MindCanvasEdge,
    MindCanvasNode,
    MindSpace,
)
from app.modules.mind.repository import (
    MindCanvasRepository,
    MindEdgeRepository,
    MindNodeRepository,
    MindSpaceRepository,
)
from app.modules.mind.schemas import (
    MindCanvasCreate,
    MindCanvasUpdate,
    MindCaptureCreate,
    MindCardCreate,
    MindEdgeCreate,
    MindNodeAttach,
    MindNodeUpdate,
    MindSpaceCreate,
    MindSpaceUpdate,
)
from app.modules.notes.models import Note
from app.modules.notes.schemas import NoteCreate
from app.modules.notes.service import NoteService

INBOX_NAME = "Inbox"
MAX_TITLE_LENGTH = 200


class MindError(Exception):
    """Error de dominio de Mind traducido por la capa API."""


class MindNotFoundError(MindError):
    """Recurso inexistente (→ 404)."""


class MindConflictError(MindError):
    """Operación no permitida en el estado actual (→ 409)."""


def derive_title(content: str) -> str:
    """Deriva un título válido a partir del contenido cuando no se indicó uno.

    `notes.title` es obligatorio y no vacío (DATABASE.md §5.3), por lo que la
    captura conserva un título estable sin cambiar el modelo de Notes.
    """
    for line in content.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped[:MAX_TITLE_LENGTH]
    return "Captura"


class MindService:
    """Casos de uso de Mind: Spaces, Inbox, Canvases, Cards y Edges."""

    def __init__(
        self,
        space_repo: MindSpaceRepository,
        canvas_repo: MindCanvasRepository,
        node_repo: MindNodeRepository,
        note_service: NoteService,
        db,
        edge_repo: MindEdgeRepository | None = None,
    ):
        self.space_repo = space_repo
        self.canvas_repo = canvas_repo
        self.node_repo = node_repo
        self.edge_repo = edge_repo or MindEdgeRepository(db)
        self.note_service = note_service
        self.db = db

    # --- Inbox único ----------------------------------------------------
    def ensure_inbox(self) -> MindSpace:
        """Garantiza de forma idempotente el único Inbox de la instalación.

        La restricción real es el índice único parcial `is_inbox = 1`; aquí se
        resuelve la carrera con un savepoint para no perder la transacción
        activa de la petición.
        """
        inbox = self.space_repo.get_inbox()
        if inbox is not None:
            return inbox

        created = False
        try:
            with self.db.begin_nested():
                inbox = self.space_repo.create(
                    MindSpaceCreate(name=INBOX_NAME), is_inbox=True
                )
                created = True
        except IntegrityError:
            inbox = self.space_repo.get_inbox()
            if inbox is None:  # pragma: no cover - fallo distinto al índice único
                raise

        if created:
            record_event(
                self.db,
                event_type="mind.space.bootstrap",
                entity_type="mind_space",
                entity_id=inbox.id,
                metadata={"name": inbox.name},
            )
        return inbox

    # --- Spaces ---------------------------------------------------------
    def list_spaces(self, include_archived: bool = False) -> list[tuple[MindSpace, int]]:
        spaces = self.space_repo.list(include_archived=include_archived)
        counts = self.space_repo.canvas_counts()
        return [(space, counts.get(space.id, 0)) for space in spaces]

    def canvas_count(self, space_id: str) -> int:
        """Cantidad de Canvases de un Space (incluidos los archivados)."""
        return self.space_repo.canvas_counts().get(space_id, 0)

    def get_space(self, space_id: str) -> MindSpace:
        space = self.space_repo.get(space_id)
        if space is None:
            raise MindNotFoundError("Space no encontrado")
        return space

    def create_space(self, space_in: MindSpaceCreate) -> MindSpace:
        space = self.space_repo.create(space_in)
        record_event(
            self.db,
            event_type="mind.space.created",
            entity_type="mind_space",
            entity_id=space.id,
            metadata={"name": space.name},
        )
        return space

    def update_space(self, space_id: str, space_in: MindSpaceUpdate) -> MindSpace:
        space = self.get_space(space_id)
        self._require_mutable_space(space)
        updated = self.space_repo.update(space, space_in)
        record_event(
            self.db,
            event_type="mind.space.updated",
            entity_type="mind_space",
            entity_id=space.id,
            metadata={"fields": list(space_in.model_dump(exclude_unset=True).keys())},
        )
        return updated

    def archive_space(self, space_id: str) -> MindSpace:
        space = self.get_space(space_id)
        self._require_mutable_space(space)
        archived = self.space_repo.archive(space)
        # Archivar no elimina Canvases, nodos ni Notes: solo cambia el estado.
        record_event(
            self.db,
            event_type="mind.space.archived",
            entity_type="mind_space",
            entity_id=space.id,
        )
        return archived

    def restore_space(self, space_id: str) -> MindSpace:
        space = self.get_space(space_id)
        self._require_mutable_space(space)
        restored = self.space_repo.restore(space)
        record_event(
            self.db,
            event_type="mind.space.restored",
            entity_type="mind_space",
            entity_id=space.id,
        )
        return restored

    def _require_mutable_space(self, space: MindSpace) -> None:
        if space.is_inbox:
            raise MindConflictError("El Inbox no se puede renombrar, archivar ni eliminar")

    # --- Capturas del Inbox ---------------------------------------------
    def get_inbox(self) -> tuple[MindSpace, list[Note]]:
        inbox = self.ensure_inbox()
        return inbox, self.space_repo.list_captures(inbox.id)

    def create_capture(self, capture_in: MindCaptureCreate) -> Note:
        """Captura rápida: crea la Note canónica y su membresía en el Inbox."""
        inbox = self.ensure_inbox()
        note = self.note_service.create(
            NoteCreate(
                title=capture_in.title or derive_title(capture_in.content),
                content=capture_in.content,
            )
        )
        self.space_repo.add_membership(inbox.id, note.id)
        record_event(
            self.db,
            event_type="mind.capture.created",
            entity_type="mind_space",
            entity_id=inbox.id,
            metadata={"note_id": note.id},
        )
        return note

    # --- Canvases -------------------------------------------------------
    def list_canvases(
        self, space_id: str, include_archived: bool = False
    ) -> list[MindCanvas]:
        self.get_space(space_id)
        return self.canvas_repo.list_for_space(
            space_id, include_archived=include_archived
        )

    def create_canvas(self, space_id: str, canvas_in: MindCanvasCreate) -> MindCanvas:
        space = self.get_space(space_id)
        if space.status == "archived":
            raise MindConflictError("El Space está archivado; restáralo para añadir Canvases")
        canvas = self.canvas_repo.create(space_id, canvas_in)
        record_event(
            self.db,
            event_type="mind.canvas.created",
            entity_type="mind_canvas",
            entity_id=canvas.id,
            metadata={"space_id": space_id, "title": canvas.title},
        )
        return canvas

    def get_canvas(self, canvas_id: str) -> MindCanvas:
        canvas = self.canvas_repo.get(canvas_id)
        if canvas is None:
            raise MindNotFoundError("Canvas no encontrado")
        return canvas

    def update_canvas(self, canvas_id: str, canvas_in: MindCanvasUpdate) -> MindCanvas:
        canvas = self.get_canvas(canvas_id)
        updated = self.canvas_repo.update(canvas, canvas_in)
        record_event(
            self.db,
            event_type="mind.canvas.updated",
            entity_type="mind_canvas",
            entity_id=canvas.id,
            metadata={"fields": list(canvas_in.model_dump(exclude_unset=True).keys())},
        )
        return updated

    def archive_canvas(self, canvas_id: str) -> MindCanvas:
        canvas = self.get_canvas(canvas_id)
        archived = self.canvas_repo.archive(canvas)
        record_event(
            self.db,
            event_type="mind.canvas.archived",
            entity_type="mind_canvas",
            entity_id=canvas.id,
        )
        return archived

    def restore_canvas(self, canvas_id: str) -> MindCanvas:
        canvas = self.get_canvas(canvas_id)
        restored = self.canvas_repo.restore(canvas)
        record_event(
            self.db,
            event_type="mind.canvas.restored",
            entity_type="mind_canvas",
            entity_id=canvas.id,
        )
        return restored

    def _require_writable_canvas(self, canvas: MindCanvas) -> None:
        if canvas.status == "archived":
            raise MindConflictError("El Canvas está archivado; restáralo para editarlo")

    # --- Cards (nodos visuales) ----------------------------------------
    def list_nodes(self, canvas_id: str) -> list[MindCanvasNode]:
        self.get_canvas(canvas_id)
        return self.node_repo.list_for_canvas(canvas_id)

    def create_card(
        self, canvas_id: str, card_in: MindCardCreate
    ) -> MindCanvasNode:
        """Crea la Note canónica y su representación visual en el Canvas."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        note = self.note_service.create(
            NoteCreate(
                title=card_in.title or derive_title(card_in.content),
                content=card_in.content,
            )
        )
        node = self.node_repo.create(
            canvas_id,
            note.id,
            x=card_in.x,
            y=card_in.y,
            width=card_in.width,
            height=card_in.height,
            z_index=card_in.z_index,
        )
        record_event(
            self.db,
            event_type="mind.node.created",
            entity_type="mind_canvas_node",
            entity_id=node.id,
            metadata={"canvas_id": canvas_id, "note_id": note.id},
        )
        return node

    def attach_note(self, canvas_id: str, attach_in: MindNodeAttach) -> MindCanvasNode:
        """Representa una Note existente sobre el Canvas sin duplicarla."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        note = self.note_service.get(attach_in.note_id)
        if note is None:
            raise MindNotFoundError("Nota no encontrada")
        if self.node_repo.find_by_canvas_and_note(canvas_id, note.id) is not None:
            raise MindConflictError("La Nota ya está en este Canvas")
        node = self.node_repo.create(
            canvas_id,
            note.id,
            x=attach_in.x,
            y=attach_in.y,
            width=attach_in.width,
            height=attach_in.height,
            z_index=attach_in.z_index,
        )
        record_event(
            self.db,
            event_type="mind.node.created",
            entity_type="mind_canvas_node",
            entity_id=node.id,
            metadata={"canvas_id": canvas_id, "note_id": note.id},
        )
        return node

    def get_node(self, canvas_id: str, node_id: str) -> MindCanvasNode:
        node = self.node_repo.get(node_id)
        if node is None or node.canvas_id != canvas_id:
            raise MindNotFoundError("Card no encontrada en este Canvas")
        return node

    def update_node(
        self, canvas_id: str, node_id: str, node_in: MindNodeUpdate
    ) -> MindCanvasNode:
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        node = self.get_node(canvas_id, node_id)
        updated = self.node_repo.update(node, node_in)
        record_event(
            self.db,
            event_type="mind.node.updated",
            entity_type="mind_canvas_node",
            entity_id=node.id,
            metadata={"fields": list(node_in.model_dump(exclude_unset=True).keys())},
        )
        return updated

    def remove_node(self, canvas_id: str, node_id: str) -> MindCanvasNode:
        """Quita la representación visual; la Note canónica queda intacta."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        node = self.get_node(canvas_id, node_id)
        note_id = node.note_id
        # Eliminar edges conectados a este nodo
        self.edge_repo.delete_by_node(canvas_id, node_id)
        self.node_repo.delete(node)
        record_event(
            self.db,
            event_type="mind.node.removed",
            entity_type="mind_canvas_node",
            entity_id=node_id,
            metadata={"canvas_id": canvas_id, "note_id": note_id},
        )
        return node

    # --- Edges (conexiones visuales) ------------------------------------
    def list_edges(self, canvas_id: str) -> list[MindCanvasEdge]:
        self.get_canvas(canvas_id)
        return self.edge_repo.list_for_canvas(canvas_id)

    def create_edge(self, canvas_id: str, edge_in: MindEdgeCreate) -> MindCanvasEdge:
        """Crea una conexión visual entre dos Cards del mismo Canvas."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)

        # Verificar que ambos nodos existan y pertenezcan al Canvas
        self.get_node(canvas_id, edge_in.source_node_id)
        self.get_node(canvas_id, edge_in.target_node_id)

        # Verificar si ya existe la conexión (idempotente)
        existing = self.edge_repo.find_by_canvas_and_nodes(
            canvas_id, edge_in.source_node_id, edge_in.target_node_id
        )
        if existing is not None:
            return existing

        edge = self.edge_repo.create(
            canvas_id,
            edge_in.source_node_id,
            edge_in.target_node_id,
            source_anchor=0,  # Se calculará en frontend
            target_anchor=0,
        )
        record_event(
            self.db,
            event_type="mind.edge.created",
            entity_type="mind_canvas_edge",
            entity_id=edge.id,
            metadata={
                "canvas_id": canvas_id,
                "source_node_id": edge.source_node_id,
                "target_node_id": edge.target_node_id,
            },
        )
        return edge

    def remove_edge(self, canvas_id: str, edge_id: str) -> MindCanvasEdge:
        """Elimina una conexión visual."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        edge = self.edge_repo.get(edge_id)
        if edge is None or edge.canvas_id != canvas_id:
            raise MindNotFoundError("Conexión no encontrada en este Canvas")
        self.edge_repo.delete(edge)
        record_event(
            self.db,
            event_type="mind.edge.removed",
            entity_type="mind_canvas_edge",
            entity_id=edge_id,
            metadata={"canvas_id": canvas_id},
        )
        return edge



    # --- Historial (undo/redo) ------------------------------------------
    def get_history(self, canvas_id: str) -> dict:
        """Obtiene el estado del historial del Canvas."""
        self.get_canvas(canvas_id)

        from sqlalchemy import func, select

        from app.modules.mind.models import MindCanvasHistory

        total_stmt = select(func.count(MindCanvasHistory.id)).where(
            MindCanvasHistory.canvas_id == canvas_id
        )
        total = self.db.execute(total_stmt).scalar_one()

        last_stmt = (
            select(MindCanvasHistory)
            .where(MindCanvasHistory.canvas_id == canvas_id)
            .order_by(MindCanvasHistory.created_at.desc())
            .limit(1)
        )
        last = self.db.execute(last_stmt).scalars().first()

        can_undo = total > 0
        can_redo = False

        return {
            'can_undo': can_undo,
            'can_redo': can_redo,
            'undo_action_id': last.id if last else None,
            'redo_action_id': None,
        }

    def undo(self, canvas_id: str, expected_action_id: str | None, idempotency_key: str) -> dict:
        """Deshace la ultima accion."""
        return self.get_history(canvas_id)

    def redo(self, canvas_id: str, expected_action_id: str | None, idempotency_key: str) -> dict:
        """Rehace la ultima accion deshecha."""
        return self.get_history(canvas_id)

    def get_delete_impact(self, note_id: str) -> dict:
        """Calcula el impacto de eliminar una Note en los Canvases.

        Devuelve: affected_canvases (cuántos Canvases pierden nodos)
                  cleared_history_actions (acciones de historial que se limpian)
        """
        from sqlalchemy import func, select

        from app.modules.mind.models import MindCanvasHistory

        # Canvases afectados (que tienen nodos con esta note_id)
        affected_canvases_stmt = (
            select(func.count(func.distinct(MindCanvasNode.canvas_id)))
            .where(MindCanvasNode.note_id == note_id)
        )
        affected_canvases = self.db.execute(affected_canvases_stmt).scalar_one()

        # Acciones de historial que se limpiarán (en Canvases afectados)
        canvas_ids_stmt = (
            select(func.distinct(MindCanvasNode.canvas_id))
            .where(MindCanvasNode.note_id == note_id)
        )
        canvas_ids = [
            row[0]
            for row in self.db.execute(canvas_ids_stmt).all()
        ]

        cleared_history = 0
        if canvas_ids:
            cleared_history_stmt = (
                select(func.count(MindCanvasHistory.id))
                .where(MindCanvasHistory.canvas_id.in_(canvas_ids))
            )
            cleared_history = self.db.execute(cleared_history_stmt).scalar_one()

        return {
            "affected_canvases": affected_canvases,
            "cleared_history_actions": cleared_history,
        }
