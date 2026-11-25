"""Esquemas Pydantic para Mind (MIND-002/003)."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


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

    @field_validator("target_node_id")
    @classmethod
    def different_nodes(cls, value: str, info) -> str:
        if info.data.get("source_node_id") == value:
            raise ValueError("Una Card no puede conectarse a sí misma")
        return value


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
    """Transición de historial (undo/redo) con clave idempotente."""

    expected_action_id: str | None = Field(default=None, max_length=36)
    idempotency_key: str = Field(..., min_length=1, max_length=64)


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
    action_type: str
    snapshot_json: str
    inverse_json: str | None = None
    request_key: str | None = None
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
    "MindCaptureCreate",
    "MindInboxOut",
    "MindHistoryTransition",
    "MindHistoryOut",
    "MindCanvasHistoryOut",
]
