"""Esquemas Pydantic para Notas, etiquetas y vínculos."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(default="", max_length=100000)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El título de la nota no puede estar vacío")
        return value.strip()


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, max_length=100000)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("El título de la nota no puede estar vacío")
        return value.strip() if value else value


class NoteOut(NoteBase):
    id: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El nombre de la etiqueta no puede estar vacío")
        return value.strip()


class TagCreate(TagBase):
    pass


class TagOut(TagBase):
    id: str
    normalized_name: str
    created_at: str

    model_config = {"from_attributes": True}


class LinkRequest(BaseModel):
    """Cuerpo para asignar/quitar vínculos (proyecto, tarea o etiqueta)."""
    id: str = Field(..., min_length=1)


class NoteLinkOut(BaseModel):
    note_id: str
    linked_id: str


__all__ = [
    "NoteBase",
    "NoteCreate",
    "NoteUpdate",
    "NoteOut",
    "TagBase",
    "TagCreate",
    "TagOut",
    "LinkRequest",
    "NoteLinkOut",
]