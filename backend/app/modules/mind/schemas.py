"""Esquemas Pydantic para Mind (MIND-002/003)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def _clean_title(value: str | None) -> str | None:
    """Normaliza un título opcional: vacío o en blanco → None."""
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None


class MindSpaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El nombre del Space no puede estar vacío")
        return value.strip()


class MindSpaceCreate(MindSpaceBase):
    pass


class MindSpaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("El nombre del Space no puede estar vacío")
        return value.strip() if value else value


class MindSpaceOut(MindSpaceBase):
    id: str
    is_inbox: bool
    status: str
    archived_at: str | None = None
    created_at: str
    updated_at: str
    canvas_count: int = 0

    model_config = {"from_attributes": True}


class MindCanvasBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El título del Canvas no puede estar vacío")
        return value.strip()


class MindCanvasCreate(MindCanvasBase):
    pass


class MindCanvasUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("El título del Canvas no puede estar vacío")
        return value.strip() if value else value


class MindCanvasOut(MindCanvasBase):
    id: str
    space_id: str
    status: str
    archived_at: str | None = None
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MindPositionBase(BaseModel):
    """Posición y tamaño en coordenadas del mundo (independientes del viewport)."""

    x: float = Field(default=0.0, ge=-100000, le=100000)
    y: float = Field(default=0.0, ge=-100000, le=100000)
    width: float | None = Field(default=None, gt=0, le=10000)
    height: float | None = Field(default=None, gt=0, le=10000)
    z_index: int | None = Field(default=None, ge=0, le=100000)


class MindCardCreate(MindPositionBase):
    """Crea una Card de texto: Note canónica + instancia visual."""

    title: str | None = Field(default=None, max_length=200)
    content: str = Field(..., min_length=1, max_length=100000)

    @field_validator("title")
    @classmethod
    def title_optional(cls, value: str | None) -> str | None:
        return _clean_title(value)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El contenido de la Card no puede estar vacío")
        return value


class MindNodeAttach(MindPositionBase):
    """Representa una Note existente sobre un Canvas (sin duplicar contenido)."""

    note_id: str = Field(..., min_length=1, max_length=36)


class MindNodeUpdate(BaseModel):
    x: float | None = Field(default=None, ge=-100000, le=100000)
    y: float | None = Field(default=None, ge=-100000, le=100000)
    width: float | None = Field(default=None, gt=0, le=10000)
    height: float | None = Field(default=None, gt=0, le=10000)
    z_index: int | None = Field(default=None, ge=0, le=100000)

    @model_validator(mode="after")
    def reject_explicit_nulls(self) -> "MindNodeUpdate":
        if any(
            field in self.model_fields_set and getattr(self, field) is None
            for field in ("x", "y", "z_index")
        ):
            raise ValueError("La posición y el orden visual no pueden ser null")
        return self


class MindNoteBrief(BaseModel):
    """Contenido canónico de la Card (una sola fuente de verdad: `notes`)."""

    id: str
    title: str
    content: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MindNodeOut(BaseModel):
    id: str
    canvas_id: str
    note_id: str
    x: float
    y: float
    width: float | None = None
    height: float | None = None
    z_index: int
    created_at: str
    updated_at: str
    note: MindNoteBrief

    model_config = {"from_attributes": True}


class MindEdgeCreate(BaseModel):
    """Crea una conexión visual entre dos Cards del mismo Canvas."""

    source_node_id: str = Field(..., min_length=1, max_length=36)
    target_node_id: str = Field(..., min_length=1, max_length=36)
    source_anchor: int = Field(default=0, ge=0, le=7)
    target_anchor: int = Field(default=0, ge=0, le=7)

    @field_validator("target_node_id")
    @classmethod
    def different_nodes(cls, value: str, info) -> str:
        if info.data.get("source_node_id") == value:
            raise ValueError("Una Card no puede conectarse a sí misma")
        return value


class MindSpatialNodeUpdate(BaseModel):
    """Cambio espacial de una Card dentro de una acción atómica."""

    id: str = Field(..., min_length=1, max_length=36)
    x: float | None = Field(default=None, ge=-100000, le=100000)
    y: float | None = Field(default=None, ge=-100000, le=100000)
    width: float | None = Field(default=None, gt=0, le=10000)
    height: float | None = Field(default=None, gt=0, le=10000)
    z_index: int | None = Field(default=None, ge=0, le=100000)


class MindSpatialActionCreate(BaseModel):
    """Acción espacial atómica para mover, redimensionar o reordenar Cards."""

    action_type: Literal["move", "resize", "reorder"]
    nodes: list[MindSpatialNodeUpdate] = Field(..., min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_spatial_fields(self) -> "MindSpatialActionCreate":
        ids = [node.id for node in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("Una acción espacial no puede repetir la misma Card")

        for node in self.nodes:
            if self.action_type == "move":
                if node.x is None or node.y is None:
                    raise ValueError("Una acción de movimiento requiere x e y")
                if (
                    node.width is not None
                    or node.height is not None
                    or node.z_index is not None
                ):
                    raise ValueError("Una acción de movimiento solo admite x e y")
            elif self.action_type == "resize":
                if node.width is None or node.height is None:
                    raise ValueError("Una acción de resize requiere width y height")
                if (
                    node.x is not None
                    or node.y is not None
                    or node.z_index is not None
                ):
                    raise ValueError("Una acción de resize solo admite width y height")
            elif node.z_index is None:
                raise ValueError("Una acción de orden requiere z_index")
            elif any(
                value is not None
                for value in (node.x, node.y, node.width, node.height)
            ):
                raise ValueError("Una acción de orden solo admite z_index")
        return self


class MindEdgeOut(BaseModel):
    id: str
    canvas_id: str
    source_node_id: str
    target_node_id: str
    source_anchor: int
    target_anchor: int
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class MindCaptureCreate(BaseModel):
    """Captura rápida del Inbox: contenido obligatorio, título opcional."""

    title: str | None = Field(default=None, max_length=200)
    content: str = Field(..., min_length=1, max_length=100000)

    @field_validator("title")
    @classmethod
    def title_optional(cls, value: str | None) -> str | None:
        return _clean_title(value)

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("La captura no puede estar vacía")
        return value


class MindInboxOut(BaseModel):
    space: MindSpaceOut
    captures: list[MindNoteBrief]

    model_config = {"from_attributes": True}


class MindHistoryTransition(BaseModel):
    """Transición de historial (undo/redo) con clave idempotente.

    La clave puede llegar en el body o en el header ``Idempotency-Key``; la
    API combina ambos y rechaza la petición si no recibe ninguna.
    """

    expected_action_id: str = Field(..., min_length=1, max_length=36)
    idempotency_key: str | None = Field(default=None, min_length=1, max_length=64)


class MindHistoryOut(BaseModel):
    """Estado del historial de un Canvas."""

    can_undo: bool
    can_redo: bool
    undo_action_id: str | None = None
    redo_action_id: str | None = None


class MindCanvasHistoryOut(BaseModel):
    """Entrada individual del historial."""

    id: str
    canvas_id: str
    sequence: int
    action_type: str
    snapshot_json: str
    inverse_json: str | None = None
    request_key: str | None = None
    state: str
    undone_at: str | None = None
    created_at: str

    model_config = {"from_attributes": True}


__all__ = [
    "MindSpaceCreate",
    "MindSpaceUpdate",
    "MindSpaceOut",
    "MindCanvasCreate",
    "MindCanvasUpdate",
    "MindCanvasOut",
    "MindPositionBase",
    "MindCardCreate",
    "MindNodeAttach",
    "MindNodeUpdate",
    "MindNoteBrief",
    "MindNodeOut",
    "MindEdgeCreate",
    "MindEdgeOut",
    "MindSpatialNodeUpdate",
    "MindSpatialActionCreate",
    "MindCaptureCreate",
    "MindInboxOut",
    "MindHistoryTransition",
    "MindHistoryOut",
    "MindCanvasHistoryOut",
]
