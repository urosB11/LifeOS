"""Servicio de Mind (MIND-002/003).

Reglas de negocio y eventos de actividad en la misma transacción que el
cambio de dominio (DATABASE.md sección 6). El contenido canónico vive en
`notes`: este módulo nunca copia ni duplica el texto de una Note.
"""

from __future__ import annotations

import hashlib
import json
import math

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.core.utils import utc_now
from app.db.activity import record_event
from app.modules.mind.models import (
    MindCanvas,
    MindCanvasEdge,
    MindCanvasHistory,
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
    MindSpatialActionCreate,
    MindSpaceCreate,
    MindSpaceUpdate,
)
from app.modules.notes.models import Note
from app.modules.notes.schemas import NoteCreate
from app.modules.notes.service import NoteService

INBOX_NAME = "Inbox"
MAX_TITLE_LENGTH = 200
HISTORY_LIMIT = 100
HISTORY_RECEIPT_ACTION = "_idempotency_receipt"


class MindError(Exception):
    """Error de dominio de Mind traducido por la capa API."""


class MindNotFoundError(MindError):
    """Recurso inexistente (→ 404)."""


class MindConflictError(MindError):
    """Operación no permitida en el estado actual (→ 409)."""


def _request_fingerprint(payload: object) -> str:
    """Huella estable para detectar reutilización incorrecta de una clave."""
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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


def _snapshot_references_note(payload: str | None, note_id: str) -> bool:
    """Indica si un snapshot del historial contiene una Card de la Note."""
    if not payload:
        return False
    try:
        envelope = json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return False
    if not isinstance(envelope, dict):
        return False

    states = []
    if isinstance(envelope.get("state"), dict):
        states.append(envelope["state"])
    if isinstance(envelope.get("nodes"), list):
        states.append(envelope)
    for state in states:
        nodes = state.get("nodes")
        if not isinstance(nodes, list):
            continue
        if any(
            isinstance(node, dict) and node.get("note_id") == note_id
            for node in nodes
        ):
            return True
    return False


def canvas_ids_referencing_note(db, note_id: str) -> set[str]:
    """Devuelve los Canvases cuyo estado actual o historial referencia la Note.

    Una Card puede haber sido quitada del Canvas y todavía estar presente en
    un snapshot reversible. Esos Canvases también deben limpiar su historial
    antes de eliminar la Note canónica.
    """
    current_canvas_ids = set(
        db.execute(
            select(MindCanvasNode.canvas_id).where(
                MindCanvasNode.note_id == note_id
            )
        )
        .scalars()
        .all()
    )
    history_rows = db.execute(
        select(
            MindCanvasHistory.canvas_id,
            MindCanvasHistory.snapshot_json,
            MindCanvasHistory.inverse_json,
        )
    ).all()
    historical_canvas_ids = {
        canvas_id
        for canvas_id, snapshot_json, inverse_json in history_rows
        if _snapshot_references_note(snapshot_json, note_id)
        or _snapshot_references_note(inverse_json, note_id)
    }
    return current_canvas_ids | historical_canvas_ids


def _is_finite_number(value: object) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _validated_canvas_snapshot(
    canvas_id: str,
    state: object,
) -> tuple[dict[str, dict], dict[str, dict]]:
    """Valida completamente un snapshot antes de modificar el Canvas."""
    node_keys = {
        "id",
        "canvas_id",
        "note_id",
        "x",
        "y",
        "width",
        "height",
        "z_index",
        "created_at",
        "updated_at",
    }
    edge_keys = {
        "id",
        "canvas_id",
        "source_node_id",
        "target_node_id",
        "source_anchor",
        "target_anchor",
        "created_at",
        "updated_at",
    }
    if (
        not isinstance(state, dict)
        or not isinstance(state.get("nodes"), list)
        or not isinstance(state.get("edges"), list)
    ):
        raise MindConflictError("El snapshot del historial no es válido")

    target_nodes: dict[str, dict] = {}
    target_note_ids: set[tuple[str, str]] = set()
    for node in state["nodes"]:
        if not isinstance(node, dict) or not node_keys.issubset(node):
            raise MindConflictError("El snapshot del historial no es válido")
        node_id = node["id"]
        note_id = node["note_id"]
        if not isinstance(node_id, str) or not node_id or len(node_id) > 36:
            raise MindConflictError("El historial contiene un ID de Card inválido")
        if node_id in target_nodes:
            raise MindConflictError("El historial contiene IDs duplicados")
        if not isinstance(note_id, str) or not note_id or len(note_id) > 36:
            raise MindConflictError("El historial contiene un ID de Note inválido")
        if node["canvas_id"] != canvas_id:
            raise MindConflictError("El historial contiene Cards de otro Canvas")
        note_key = (canvas_id, note_id)
        if note_key in target_note_ids:
            raise MindConflictError(
                "El historial contiene dos Cards de la misma Note en el Canvas"
            )
        if (
            not _is_finite_number(node["x"])
            or not _is_finite_number(node["y"])
            or not -100000 <= float(node["x"]) <= 100000
            or not -100000 <= float(node["y"]) <= 100000
        ):
            raise MindConflictError("El historial contiene coordenadas inválidas")
        for dimension in ("width", "height"):
            value = node[dimension]
            if value is not None and (
                not _is_finite_number(value)
                or not 0 < float(value) <= 10000
            ):
                raise MindConflictError("El historial contiene tamaños inválidos")
        if (
            type(node["z_index"]) is not int
            or not 0 <= node["z_index"] <= 100000
        ):
            raise MindConflictError("El historial contiene un orden inválido")
        if (
            not isinstance(node["created_at"], str)
            or not node["created_at"]
            or not isinstance(node["updated_at"], str)
            or not node["updated_at"]
        ):
            raise MindConflictError("El historial contiene timestamps inválidos")
        target_nodes[node_id] = node
        target_note_ids.add(note_key)

    target_edges: dict[str, dict] = {}
    target_pairs: set[tuple[str, str, str]] = set()
    for edge in state["edges"]:
        if not isinstance(edge, dict) or not edge_keys.issubset(edge):
            raise MindConflictError("El snapshot del historial no es válido")
        edge_id = edge["id"]
        if not isinstance(edge_id, str) or not edge_id or len(edge_id) > 36:
            raise MindConflictError("El historial contiene un ID de conexión inválido")
        if edge_id in target_edges:
            raise MindConflictError("El historial contiene IDs duplicados")
        if edge["canvas_id"] != canvas_id:
            raise MindConflictError(
                "El historial contiene conexiones de otro Canvas"
            )
        source_id = edge["source_node_id"]
        target_id = edge["target_node_id"]
        if (
            not isinstance(source_id, str)
            or not isinstance(target_id, str)
            or source_id not in target_nodes
            or target_id not in target_nodes
            or source_id >= target_id
        ):
            raise MindConflictError(
                "El historial contiene conexiones inválidas para este Canvas"
            )
        pair = (canvas_id, source_id, target_id)
        if pair in target_pairs:
            raise MindConflictError(
                "El historial contiene conexiones visuales duplicadas"
            )
        for anchor in ("source_anchor", "target_anchor"):
            value = edge[anchor]
            if type(value) is not int or not 0 <= value <= 7:
                raise MindConflictError("El historial contiene anclajes inválidos")
        if (
            not isinstance(edge["created_at"], str)
            or not edge["created_at"]
            or not isinstance(edge["updated_at"], str)
            or not edge["updated_at"]
        ):
            raise MindConflictError("El historial contiene timestamps inválidos")
        target_edges[edge_id] = edge
        target_pairs.add(pair)

    return target_nodes, target_edges


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

    # --- Historial espacial --------------------------------------------
    def _canvas_state(self, canvas_id: str) -> dict:
        """Devuelve el estado visual serializable del Canvas."""
        nodes = list(
            self.db.execute(
                select(MindCanvasNode)
                .where(MindCanvasNode.canvas_id == canvas_id)
                .order_by(MindCanvasNode.z_index, MindCanvasNode.created_at, MindCanvasNode.id)
            )
            .scalars()
            .all()
        )
        edges = list(
            self.db.execute(
                select(MindCanvasEdge)
                .where(MindCanvasEdge.canvas_id == canvas_id)
                .order_by(MindCanvasEdge.created_at, MindCanvasEdge.id)
            )
            .scalars()
            .all()
        )
        return {
            "nodes": [
                {
                    "id": node.id,
                    "canvas_id": node.canvas_id,
                    "note_id": node.note_id,
                    "x": node.x,
                    "y": node.y,
                    "width": node.width,
                    "height": node.height,
                    "z_index": node.z_index,
                    "created_at": node.created_at,
                    "updated_at": node.updated_at,
                }
                for node in nodes
            ],
            "edges": [
                {
                    "id": edge.id,
                    "canvas_id": edge.canvas_id,
                    "source_node_id": edge.source_node_id,
                    "target_node_id": edge.target_node_id,
                    "source_anchor": edge.source_anchor,
                    "target_anchor": edge.target_anchor,
                    "created_at": edge.created_at,
                    "updated_at": edge.updated_at,
                }
                for edge in edges
            ],
        }

    @staticmethod
    def _history_envelope(row: MindCanvasHistory) -> dict:
        try:
            envelope = json.loads(row.snapshot_json)
        except (TypeError, json.JSONDecodeError):
            envelope = {}
        if not isinstance(envelope, dict) or "state" not in envelope:
            envelope = {"state": envelope}
        envelope.setdefault("transitions", [])
        return envelope

    @staticmethod
    def _inverse_envelope(row: MindCanvasHistory) -> dict:
        try:
            envelope = json.loads(row.inverse_json or "{}")
        except (TypeError, json.JSONDecodeError):
            envelope = {}
        if not isinstance(envelope, dict):
            envelope = {"state": envelope}
        return envelope

    def _history_rows(self, canvas_id: str) -> list[MindCanvasHistory]:
        return list(
            self.db.execute(
                select(MindCanvasHistory)
                .where(MindCanvasHistory.canvas_id == canvas_id)
                .order_by(
                    MindCanvasHistory.sequence,
                    MindCanvasHistory.created_at,
                    MindCanvasHistory.id,
                )
            )
            .scalars()
            .all()
        )

    def _history_status(self, canvas_id: str) -> dict:
        rows = self._history_rows(canvas_id)
        undo_row = next(
            (row for row in reversed(rows) if row.state == "applied"),
            None,
        )
        redo_row = next((row for row in rows if row.state == "undone"), None)
        return {
            "can_undo": undo_row is not None,
            "can_redo": redo_row is not None,
            "undo_action_id": undo_row.id if undo_row else None,
            "redo_action_id": redo_row.id if redo_row else None,
        }

    def _discard_redo_branch(self, canvas_id: str) -> None:
        for row in self._history_rows(canvas_id):
            if row.state == "undone":
                row.state = "discarded"
                self.db.add(row)

    def _record_history(
        self,
        canvas_id: str,
        action_type: str,
        before: dict,
        after: dict,
        *,
        request_key: str | None = None,
        result: dict | None = None,
    ) -> MindCanvasHistory:
        self._discard_redo_branch(canvas_id)
        current_max = self.db.execute(
            select(func.max(MindCanvasHistory.sequence)).where(
                MindCanvasHistory.canvas_id == canvas_id
            )
        ).scalar_one()
        sequence = (current_max or 0) + 1
        envelope = {"state": before, "transitions": []}
        if result:
            envelope["result"] = result
        inverse = {"state": after}
        if result:
            inverse["result"] = result
        row = MindCanvasHistory(
            canvas_id=canvas_id,
            sequence=sequence,
            action_type=action_type,
            snapshot_json=json.dumps(envelope, ensure_ascii=False, sort_keys=True),
            inverse_json=json.dumps(inverse, ensure_ascii=False, sort_keys=True),
            request_key=request_key,
            state="applied",
        )
        self.db.add(row)
        self.db.flush()

        rows = self._history_rows(canvas_id)
        action_rows = [
            history_row
            for history_row in rows
            if history_row.action_type != HISTORY_RECEIPT_ACTION
        ]
        if len(action_rows) > HISTORY_LIMIT:
            for old_row in action_rows[: len(action_rows) - HISTORY_LIMIT]:
                if old_row.request_key:
                    # Conserva el recibo idempotente aunque la acción ya no
                    # sea deshacible. Un retry tardío no debe duplicar una Note
                    # o una Card que el usuario ya dejó fuera del historial.
                    envelope = self._history_envelope(old_row)
                    receipt = {
                        "state": {},
                        "transitions": envelope.get("transitions", []),
                    }
                    if "result" in envelope:
                        receipt["result"] = envelope["result"]
                    old_row.action_type = HISTORY_RECEIPT_ACTION
                    old_row.snapshot_json = json.dumps(
                        receipt,
                        ensure_ascii=False,
                        sort_keys=True,
                    )
                    old_row.inverse_json = None
                    old_row.state = "discarded"
                    old_row.undone_at = None
                    self.db.add(old_row)
                else:
                    self.db.delete(old_row)
            self.db.flush()
        return row

    def _idempotent_result(
        self,
        canvas_id: str,
        request_key: str | None,
        result_type: str,
        fingerprint: str | None = None,
    ) -> dict | None:
        if not request_key:
            return None
        row = self.db.execute(
            select(MindCanvasHistory).where(
                MindCanvasHistory.canvas_id == canvas_id,
                MindCanvasHistory.request_key == request_key,
            )
        ).scalar_one_or_none()
        if row is None:
            return None
        result = self._history_envelope(row).get("result")
        if not isinstance(result, dict) or result.get("type") != result_type:
            raise MindConflictError("La clave idempotente ya pertenece a otra operación")
        stored_fingerprint = result.get("fingerprint")
        if (
            fingerprint
            and stored_fingerprint
            and stored_fingerprint != fingerprint
        ):
            raise MindConflictError(
                "La clave idempotente ya se usó con una carga diferente"
            )
        return result

    def _transition_marker(
        self,
        canvas_id: str,
        idempotency_key: str,
        direction: str,
        action_id: str,
    ) -> bool:
        """Detecta un retry de undo/redo ya aplicado."""
        for row in self._history_rows(canvas_id):
            transitions = self._history_envelope(row).get("transitions", [])
            if not isinstance(transitions, list):
                continue
            for transition in transitions:
                if not isinstance(transition, dict):
                    continue
                if transition.get("key") != idempotency_key:
                    continue
                if (
                    transition.get("direction") != direction
                    or transition.get("action_id") != action_id
                ):
                    raise MindConflictError(
                        "La clave idempotente ya pertenece a otra transición"
                    )
                return True
        return False

    def _record_transition(
        self,
        row: MindCanvasHistory,
        idempotency_key: str,
        direction: str,
    ) -> None:
        envelope = self._history_envelope(row)
        transitions = envelope.get("transitions", [])
        if not isinstance(transitions, list):
            transitions = []
        transitions.append(
            {
                "key": idempotency_key,
                "direction": direction,
                "action_id": row.id,
            }
        )
        envelope["transitions"] = transitions
        row.snapshot_json = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
        self.db.add(row)
        self.db.flush()

    def _restore_canvas_state(self, canvas_id: str, state: dict) -> None:
        target_nodes, target_edges = _validated_canvas_snapshot(canvas_id, state)

        note_ids = {node["note_id"] for node in target_nodes.values()}
        if note_ids:
            existing_note_ids = set(
                self.db.execute(
                    select(Note.id).where(Note.id.in_(tuple(note_ids)))
                ).scalars().all()
            )
            missing = note_ids - existing_note_ids
            if missing:
                raise MindConflictError(
                    "El historial no puede restaurar Cards cuya Note ya no existe"
                )

        current_edges = list(
            self.db.execute(
                select(MindCanvasEdge).where(MindCanvasEdge.canvas_id == canvas_id)
            )
            .scalars()
            .all()
        )
        for edge in current_edges:
            if edge.id not in target_edges:
                self.db.delete(edge)
        self.db.flush()

        current_nodes = list(
            self.db.execute(
                select(MindCanvasNode).where(MindCanvasNode.canvas_id == canvas_id)
            )
            .scalars()
            .all()
        )
        for node in current_nodes:
            if node.id not in target_nodes:
                self.db.delete(node)
        self.db.flush()

        for node_id, values in target_nodes.items():
            node = self.db.get(MindCanvasNode, node_id)
            if node is None:
                node = MindCanvasNode(id=node_id)
                self.db.add(node)
            elif node.canvas_id != canvas_id:
                raise MindConflictError("El historial contiene una Card de otro Canvas")
            node.canvas_id = values["canvas_id"]
            node.note_id = values["note_id"]
            node.x = values["x"]
            node.y = values["y"]
            node.width = values["width"]
            node.height = values["height"]
            node.z_index = values["z_index"]
            node.created_at = values["created_at"]
            node.updated_at = values["updated_at"]
        self.db.flush()

        for edge_id, values in target_edges.items():
            pair = (
                values["canvas_id"],
                values["source_node_id"],
                values["target_node_id"],
            )
            conflicting = self.db.execute(
                select(MindCanvasEdge).where(
                    MindCanvasEdge.canvas_id == pair[0],
                    MindCanvasEdge.source_node_id == pair[1],
                    MindCanvasEdge.target_node_id == pair[2],
                    MindCanvasEdge.id != edge_id,
                )
            ).scalar_one_or_none()
            if conflicting is not None:
                self.db.delete(conflicting)
                self.db.flush()

            edge = self.db.get(MindCanvasEdge, edge_id)
            if edge is None:
                edge = MindCanvasEdge(id=edge_id)
                self.db.add(edge)
            elif edge.canvas_id != canvas_id:
                raise MindConflictError("El historial contiene una conexión de otro Canvas")
            edge.canvas_id = values["canvas_id"]
            edge.source_node_id = values["source_node_id"]
            edge.target_node_id = values["target_node_id"]
            edge.source_anchor = values["source_anchor"]
            edge.target_anchor = values["target_anchor"]
            edge.created_at = values["created_at"]
            edge.updated_at = values["updated_at"]
        self.db.flush()

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
        self,
        canvas_id: str,
        card_in: MindCardCreate,
        *,
        request_key: str | None = None,
    ) -> MindCanvasNode:
        """Crea la Note canónica y su representación visual en el Canvas."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        fingerprint = _request_fingerprint(
            {"canvas_id": canvas_id, "card": card_in.model_dump()}
        )
        existing = self._idempotent_result(
            canvas_id,
            request_key,
            "card",
            fingerprint,
        )
        if existing:
            node = self.node_repo.get(existing["id"])
            if node is None:
                raise MindConflictError("La Card de la solicitud idempotente ya no existe")
            return node

        before = self._canvas_state(canvas_id)
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
        self.db.flush()
        self._record_history(
            canvas_id,
            "create_node",
            before,
            self._canvas_state(canvas_id),
            request_key=request_key,
            result={
                "type": "card",
                "id": node.id,
                "fingerprint": fingerprint,
            },
        )
        return node

    def attach_note(
        self,
        canvas_id: str,
        attach_in: MindNodeAttach,
        *,
        request_key: str | None = None,
    ) -> MindCanvasNode:
        """Representa una Note existente sobre el Canvas sin duplicarla."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        fingerprint = _request_fingerprint(
            {"canvas_id": canvas_id, "attach": attach_in.model_dump()}
        )
        existing = self._idempotent_result(
            canvas_id,
            request_key,
            "attached_node",
            fingerprint,
        )
        if existing:
            node = self.node_repo.get(existing["id"])
            if node is None:
                raise MindConflictError(
                    "La Card de la solicitud idempotente ya no existe"
                )
            return node

        note = self.note_service.get(attach_in.note_id)
        if note is None:
            raise MindNotFoundError("Nota no encontrada")
        if self.node_repo.find_by_canvas_and_note(canvas_id, note.id) is not None:
            raise MindConflictError("La Nota ya está en este Canvas")
        before = self._canvas_state(canvas_id)
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
        self.db.flush()
        self._record_history(
            canvas_id,
            "attach_node",
            before,
            self._canvas_state(canvas_id),
            request_key=request_key,
            result={
                "type": "attached_node",
                "id": node.id,
                "fingerprint": fingerprint,
            },
        )
        return node

    def get_node(self, canvas_id: str, node_id: str) -> MindCanvasNode:
        node = self.node_repo.get(node_id)
        if node is None or node.canvas_id != canvas_id:
            raise MindNotFoundError("Card no encontrada en este Canvas")
        return node

    def update_node(
        self,
        canvas_id: str,
        node_id: str,
        node_in: MindNodeUpdate,
        *,
        request_key: str | None = None,
    ) -> MindCanvasNode:
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        fingerprint = _request_fingerprint(
            {
                "canvas_id": canvas_id,
                "node_id": node_id,
                "node": node_in.model_dump(exclude_unset=True),
            }
        )
        existing = self._idempotent_result(
            canvas_id,
            request_key,
            "node_update",
            fingerprint,
        )
        if existing:
            node = self.node_repo.get(existing["id"])
            if node is None:
                raise MindConflictError("La Card de la solicitud idempotente ya no existe")
            return node

        node = self.get_node(canvas_id, node_id)
        before = self._canvas_state(canvas_id)
        updated = self.node_repo.update(node, node_in)
        record_event(
            self.db,
            event_type="mind.node.updated",
            entity_type="mind_canvas_node",
            entity_id=node.id,
            metadata={"fields": list(node_in.model_dump(exclude_unset=True).keys())},
        )
        self.db.flush()
        self._record_history(
            canvas_id,
            "update_node",
            before,
            self._canvas_state(canvas_id),
            request_key=request_key,
            result={
                "type": "node_update",
                "id": node.id,
                "fingerprint": fingerprint,
            },
        )
        return updated

    def remove_node(
        self,
        canvas_id: str,
        node_id: str,
        *,
        request_key: str | None = None,
    ) -> MindCanvasNode | None:
        """Quita la representación visual; la Note canónica queda intacta."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        fingerprint = _request_fingerprint(
            {"canvas_id": canvas_id, "node_id": node_id}
        )
        existing = self._idempotent_result(
            canvas_id,
            request_key,
            "node_remove",
            fingerprint,
        )
        if existing:
            return None

        node = self.get_node(canvas_id, node_id)
        note_id = node.note_id
        before = self._canvas_state(canvas_id)
        self.edge_repo.delete_by_node(canvas_id, node_id)
        self.node_repo.delete(node)
        record_event(
            self.db,
            event_type="mind.node.removed",
            entity_type="mind_canvas_node",
            entity_id=node_id,
            metadata={"canvas_id": canvas_id, "note_id": note_id},
        )
        self.db.flush()
        self._record_history(
            canvas_id,
            "remove_node",
            before,
            self._canvas_state(canvas_id),
            request_key=request_key,
            result={
                "type": "node_remove",
                "id": node_id,
                "fingerprint": fingerprint,
            },
        )
        return node

    def apply_spatial_action(
        self,
        canvas_id: str,
        action_in: MindSpatialActionCreate,
        *,
        request_key: str | None = None,
    ) -> dict:
        """Aplica una acción espacial indivisible y reversible."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        fingerprint = _request_fingerprint(
            {"canvas_id": canvas_id, "action": action_in.model_dump()}
        )
        existing = self._idempotent_result(
            canvas_id,
            request_key,
            "spatial_action",
            fingerprint,
        )
        if existing:
            return self._history_status(canvas_id)

        before = self._canvas_state(canvas_id)
        current_nodes = {
            node.id: node
            for node in self.db.execute(
                select(MindCanvasNode).where(
                    MindCanvasNode.canvas_id == canvas_id
                )
            )
            .scalars()
            .all()
        }
        missing = [
            update.id for update in action_in.nodes if update.id not in current_nodes
        ]
        if missing:
            raise MindNotFoundError(
                "Una Card de la acción no pertenece a este Canvas: "
                + ", ".join(missing)
            )

        if action_in.action_type == "reorder":
            ordered = sorted(
                self.db.execute(
                    select(MindCanvasNode)
                    .where(MindCanvasNode.canvas_id == canvas_id)
                    .order_by(
                        MindCanvasNode.z_index,
                        MindCanvasNode.created_at,
                        MindCanvasNode.id,
                    )
                )
                .scalars()
                .all(),
                key=lambda node: (node.z_index, node.created_at, node.id),
            )
            for update in action_in.nodes:
                node = next(item for item in ordered if item.id == update.id)
                ordered.remove(node)
                target = min(max(update.z_index or 0, 0), len(ordered))
                ordered.insert(target, node)
            for index, node in enumerate(ordered):
                node.z_index = index
                self.db.add(node)
        else:
            for update in action_in.nodes:
                node = self.db.get(MindCanvasNode, update.id)
                if node is None or node.canvas_id != canvas_id:
                    raise MindNotFoundError(
                        "Una Card de la acción no pertenece a este Canvas"
                    )
                if action_in.action_type == "move":
                    node.x = update.x
                    node.y = update.y
                else:
                    node.width = update.width
                    node.height = update.height
                self.db.add(node)

        self.db.flush()
        after = self._canvas_state(canvas_id)
        self._record_history(
            canvas_id,
            f"spatial_{action_in.action_type}",
            before,
            after,
            request_key=request_key,
            result={
                "type": "spatial_action",
                "fingerprint": fingerprint,
            },
        )
        record_event(
            self.db,
            event_type="mind.canvas.spatial_action",
            entity_type="mind_canvas",
            entity_id=canvas_id,
            metadata={
                "action_type": action_in.action_type,
                "node_ids": [update.id for update in action_in.nodes],
            },
        )
        return self._history_status(canvas_id)

    # --- Edges (conexiones visuales) ------------------------------------
    def list_edges(self, canvas_id: str) -> list[MindCanvasEdge]:
        self.get_canvas(canvas_id)
        return self.edge_repo.list_for_canvas(canvas_id)

    def create_edge(
        self,
        canvas_id: str,
        edge_in: MindEdgeCreate,
        *,
        request_key: str | None = None,
    ) -> MindCanvasEdge:
        """Crea una conexión visual entre dos Cards del mismo Canvas."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        fingerprint = _request_fingerprint(
            {"canvas_id": canvas_id, "edge": edge_in.model_dump()}
        )
        existing = self._idempotent_result(
            canvas_id,
            request_key,
            "edge",
            fingerprint,
        )
        if existing:
            edge = self.edge_repo.get(existing["id"])
            if edge is None:
                raise MindConflictError(
                    "La conexión de la solicitud idempotente ya no existe"
                )
            return edge

        self.get_node(canvas_id, edge_in.source_node_id)
        self.get_node(canvas_id, edge_in.target_node_id)

        duplicate = self.edge_repo.find_by_canvas_and_nodes(
            canvas_id, edge_in.source_node_id, edge_in.target_node_id
        )
        if duplicate is not None:
            raise MindConflictError("Las Cards ya están conectadas")

        before = self._canvas_state(canvas_id)
        edge = self.edge_repo.create(
            canvas_id,
            edge_in.source_node_id,
            edge_in.target_node_id,
            source_anchor=edge_in.source_anchor,
            target_anchor=edge_in.target_anchor,
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
        self.db.flush()
        self._record_history(
            canvas_id,
            "create_edge",
            before,
            self._canvas_state(canvas_id),
            request_key=request_key,
            result={
                "type": "edge",
                "id": edge.id,
                "fingerprint": fingerprint,
            },
        )
        return edge

    def remove_edge(
        self,
        canvas_id: str,
        edge_id: str,
        *,
        request_key: str | None = None,
    ) -> MindCanvasEdge | None:
        """Elimina una conexión visual."""
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        fingerprint = _request_fingerprint(
            {"canvas_id": canvas_id, "edge_id": edge_id}
        )
        existing = self._idempotent_result(
            canvas_id,
            request_key,
            "edge_remove",
            fingerprint,
        )
        if existing:
            return None

        edge = self.edge_repo.get(edge_id)
        if edge is None or edge.canvas_id != canvas_id:
            raise MindNotFoundError("Conexión no encontrada en este Canvas")
        before = self._canvas_state(canvas_id)
        self.edge_repo.delete(edge)
        record_event(
            self.db,
            event_type="mind.edge.removed",
            entity_type="mind_canvas_edge",
            entity_id=edge_id,
            metadata={"canvas_id": canvas_id},
        )
        self.db.flush()
        self._record_history(
            canvas_id,
            "remove_edge",
            before,
            self._canvas_state(canvas_id),
            request_key=request_key,
            result={
                "type": "edge_remove",
                "id": edge_id,
                "fingerprint": fingerprint,
            },
        )
        return edge



    # --- Historial (undo/redo) ------------------------------------------
    def get_history(self, canvas_id: str) -> dict:
        """Obtiene el estado del historial del Canvas."""
        self.get_canvas(canvas_id)
        return self._history_status(canvas_id)

    def _transition_history(
        self,
        canvas_id: str,
        direction: str,
        expected_action_id: str,
        idempotency_key: str,
    ) -> dict:
        canvas = self.get_canvas(canvas_id)
        self._require_writable_canvas(canvas)
        if not idempotency_key:
            raise MindConflictError("La transición requiere una clave idempotente")

        if self._transition_marker(
            canvas_id,
            idempotency_key,
            direction,
            expected_action_id,
        ):
            return self._history_status(canvas_id)

        rows = self._history_rows(canvas_id)
        if direction == "undo":
            target = next(
                (row for row in reversed(rows) if row.state == "applied"),
                None,
            )
            target_state = self._history_envelope(target).get("state") if target else None
        else:
            target = next((row for row in rows if row.state == "undone"), None)
            target_state = (
                self._inverse_envelope(target).get("state") if target else None
            )

        if target is None:
            action = "deshacer" if direction == "undo" else "rehacer"
            raise MindConflictError(f"No hay una acción para {action}")
        if target.id != expected_action_id:
            raise MindConflictError("El historial avanzó; la acción esperada ya no está vigente")

        self._restore_canvas_state(canvas_id, target_state or {})
        if direction == "undo":
            target.state = "undone"
            target.undone_at = utc_now()
        else:
            target.state = "applied"
            target.undone_at = None
        self.db.add(target)
        self.db.flush()
        self._record_transition(target, idempotency_key, direction)
        record_event(
            self.db,
            event_type=f"mind.canvas.history.{direction}",
            entity_type="mind_canvas",
            entity_id=canvas_id,
            metadata={"action_id": target.id},
        )
        return self._history_status(canvas_id)

    def undo(
        self,
        canvas_id: str,
        expected_action_id: str,
        idempotency_key: str,
    ) -> dict:
        """Deshace la última acción aplicada del Canvas."""
        return self._transition_history(
            canvas_id,
            "undo",
            expected_action_id,
            idempotency_key,
        )

    def redo(
        self,
        canvas_id: str,
        expected_action_id: str,
        idempotency_key: str,
    ) -> dict:
        """Rehace la siguiente acción deshecha del Canvas."""
        return self._transition_history(
            canvas_id,
            "redo",
            expected_action_id,
            idempotency_key,
        )

    def get_delete_impact(self, note_id: str) -> dict:
        """Calcula el impacto de eliminar una Note en los Canvases.

        Devuelve: affected_canvases (Canvases con Cards actuales o snapshots)
                  cleared_history_actions (acciones que se limpiarán)
        """
        from sqlalchemy import func, select

        from app.modules.mind.models import MindCanvasHistory

        canvas_ids = canvas_ids_referencing_note(self.db, note_id)
        cleared_history = 0
        if canvas_ids:
            cleared_history = self.db.execute(
                select(func.count(MindCanvasHistory.id)).where(
                    MindCanvasHistory.canvas_id.in_(tuple(canvas_ids))
                )
            ).scalar_one()

        return {
            "affected_canvases": len(canvas_ids),
            "cleared_history_actions": cleared_history,
        }
