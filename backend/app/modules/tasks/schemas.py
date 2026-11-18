"""Esquemas Pydantic para Tareas."""

from pydantic import BaseModel, Field, field_validator


class TaskBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: str = Field(default="pending")
    priority: str | None = Field(default=None, max_length=10)
    due_date: str | None = Field(default=None, max_length=10)
    project_id: str | None = Field(default=None, max_length=36)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El título de la tarea no puede estar vacío")
        return value.strip()

    @field_validator("status")
    @classmethod
    def status_valid(cls, value: str) -> str:
        allowed = {"pending", "completed"}
        if value not in allowed:
            raise ValueError(f"Estado inválido: {value}. Valores permitidos: {sorted(allowed)}")
        return value

    @field_validator("priority")
    @classmethod
    def priority_valid(cls, value: str | None) -> str | None:
        if value is not None:
            allowed = {"low", "normal", "high"}
            if value not in allowed:
                raise ValueError(
                    f"Prioridad inválida: {value}. Valores permitidos: {sorted(allowed)}"
                )
        return value

    @field_validator("due_date")
    @classmethod
    def due_date_format(cls, value: str | None) -> str | None:
        if value is not None:
            import re

            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError("La fecha de vencimiento debe tener formato YYYY-MM-DD")
        return value


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None)
    priority: str | None = Field(default=None, max_length=10)
    due_date: str | None = Field(default=None, max_length=10)
    project_id: str | None = Field(default=None, max_length=36)

    @field_validator("title")
    @classmethod
    def title_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("El título de la tarea no puede estar vacío")
        return value.strip() if value else value

    @field_validator("status")
    @classmethod
    def status_valid(cls, value: str | None) -> str | None:
        if value is not None:
            allowed = {"pending", "completed"}
            if value not in allowed:
                raise ValueError(
                    f"Estado inválido: {value}. Valores permitidos: {sorted(allowed)}"
                )
        return value

    @field_validator("priority")
    @classmethod
    def priority_valid(cls, value: str | None) -> str | None:
        if value is not None:
            allowed = {"low", "normal", "high"}
            if value not in allowed:
                raise ValueError(
                    f"Prioridad inválida: {value}. Valores permitidos: {sorted(allowed)}"
                )
        return value

    @field_validator("due_date")
    @classmethod
    def due_date_format(cls, value: str | None) -> str | None:
        if value is not None:
            import re

            if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
                raise ValueError("La fecha de vencimiento debe tener formato YYYY-MM-DD")
        return value


class TaskOut(TaskBase):
    id: str
    created_at: str
    updated_at: str
    completed_at: str | None = None

    model_config = {"from_attributes": True}


__all__ = ["TaskBase", "TaskCreate", "TaskUpdate", "TaskOut"]