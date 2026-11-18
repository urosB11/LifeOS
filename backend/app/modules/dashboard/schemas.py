"""Esquemas Pydantic para Dashboard y configuración."""

from __future__ import annotations

from pydantic import BaseModel, Field


class WidgetPreferenceBase(BaseModel):
    is_visible: bool = Field(default=True)
    position: int = Field(default=0, ge=0)
    config_json: str | None = Field(default=None, max_length=10000)


class WidgetPreferenceCreate(WidgetPreferenceBase):
    pass


class WidgetPreferenceUpdate(BaseModel):
    is_visible: bool | None = Field(default=None)
    position: int | None = Field(default=None, ge=0)
    config_json: str | None = Field(default=None, max_length=10000)


class WidgetPreferenceOut(WidgetPreferenceBase):
    widget_id: str
    updated_at: str

    model_config = {"from_attributes": True}


class WidgetCatalogItem(BaseModel):
    """Elemento del catálogo de widgets definido en código."""

    widget_id: str
    label: str
    description: str
    default_visible: bool
    default_position: int


class UserPreferenceBase(BaseModel):
    value: str


class UserPreferenceCreate(UserPreferenceBase):
    pass


class UserPreferenceUpdate(BaseModel):
    value: str


class UserPreferenceOut(UserPreferenceBase):
    key: str
    updated_at: str

    model_config = {"from_attributes": True}


class ThemeRequest(BaseModel):
    theme: str = Field(..., pattern="^(system|light|dark)$")


class TimezoneRequest(BaseModel):
    timezone: str = Field(..., min_length=1, max_length=100)


__all__ = [
    "WidgetPreferenceBase",
    "WidgetPreferenceCreate",
    "WidgetPreferenceUpdate",
    "WidgetPreferenceOut",
    "WidgetCatalogItem",
    "UserPreferenceBase",
    "UserPreferenceCreate",
    "UserPreferenceUpdate",
    "UserPreferenceOut",
    "ThemeRequest",
    "TimezoneRequest",
]