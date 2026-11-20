"""Esquemas Pydantic para Proyectos."""

from pydantic import BaseModel, Field, field_validator


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: str = Field(default="active")

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return value.strip()

    @field_validator("status")
    @classmethod
    def status_valid(cls, value: str) -> str:
        allowed = {"active", "completed", "archived"}
        if value not in allowed:
            raise ValueError(f"Estado inválido: {value}. Valores permitidos: {sorted(allowed)}")
        return value


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: str | None = Field(default=None)

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("El nombre del proyecto no puede estar vacío")
        return value.strip() if value else value

    @field_validator("status")
    @classmethod
    def status_valid(cls, value: str | None) -> str | None:
        if value is not None:
            allowed = {"active", "completed", "archived"}
            if value not in allowed:
                raise ValueError(
                    f"Estado inválido: {value}. Valores permitidos: {sorted(allowed)}"
                )
        return value


class ProjectOut(ProjectBase):
    id: str
    created_at: str
    updated_at: str
    completed_at: str | None = None
    archived_at: str | None = None
    task_count: int = 0
    completed_count: int = 0
    overdue_count: int = 0
    next_due_date: str | None = None

    model_config = {"from_attributes": True}


__all__ = ["ProjectBase", "ProjectCreate", "ProjectUpdate", "ProjectOut"]