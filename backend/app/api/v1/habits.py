"""Rutas API de Hábitos (Fase 7)."""

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.db.session import get_db
from app.modules.habits.repository import HabitEntryRepository, HabitRepository
from app.modules.habits.schemas import (
    EntryCreate,
    EntryOut,
    EntryUpdate,
    HabitCreate,
    HabitOut,
    HabitStats,
    HabitUpdate,
    TodayItem,
    WeekView,
)
from app.modules.habits.service import ConflictError, HabitService

router = APIRouter(prefix="/habits", tags=["habits"])


def _service(db=Depends(get_db)) -> HabitService:
    return HabitService(
        habit_repo=HabitRepository(db),
        entry_repo=HabitEntryRepository(db),
        db=db,
    )


def _habit_or_404(habit: HabitOut | None) -> HabitOut:
    if habit is None:
        raise HTTPException(status_code=404, detail="Hábito no encontrado")
    return habit


@router.post("", response_model=HabitOut, status_code=status.HTTP_201_CREATED)
def create_habit(habit_in: HabitCreate, service: HabitService = Depends(_service)):
    """Crea un nuevo hábito."""
    try:
        return service.create(habit_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("", response_model=list[HabitOut])
def list_habits(
    status: str | None = None,
    category: str | None = None,
    service: HabitService = Depends(_service),
):
    """Lista hábitos con filtros opcionales por estado y categoría."""
    return service.list(status=status, category=category)


# /habits/today y /habits/stats deben declararse antes de /habits/{habit_id}
# para no ser capturados como un ID.
@router.get("/today", response_model=list[TodayItem])
def habits_today(service: HabitService = Depends(_service)):
    """Hábitos activos programados para el día local actual, con su registro."""
    return service.today()


@router.get("/stats", response_model=list[HabitStats])
def habits_stats(
    habit_id: str | None = None,
    service: HabitService = Depends(_service),
):
    """Métricas (rachas y cumplimiento) de un hábito o de todos los no archivados."""
    try:
        return service.stats(habit_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.get("/week", response_model=WeekView)
def habits_week(service: HabitService = Depends(_service)):
    """Semana local en curso con programación y registro por hábito."""
    return service.week()


@router.get("/{habit_id}", response_model=HabitOut)
def get_habit(habit_id: str, service: HabitService = Depends(_service)):
    """Obtiene un hábito por su ID."""
    return _habit_or_404(service.get(habit_id))


@router.patch("/{habit_id}", response_model=HabitOut)
def update_habit(
    habit_id: str,
    habit_in: HabitUpdate,
    service: HabitService = Depends(_service),
):
    """Actualiza un hábito existente (nombre, frecuencia, objetivo, orden...)."""
    try:
        habit = service.update(habit_id, habit_in)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _habit_or_404(habit)


def _transition_route(habit_id: str, service: HabitService, action: str) -> HabitOut:
    try:
        return getattr(service, action)(habit_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="Hábito no encontrado")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.post("/{habit_id}/pause", response_model=HabitOut)
def pause_habit(habit_id: str, service: HabitService = Depends(_service)):
    """Pausa un hábito activo."""
    return _transition_route(habit_id, service, "pause")


@router.post("/{habit_id}/resume", response_model=HabitOut)
def resume_habit(habit_id: str, service: HabitService = Depends(_service)):
    """Reactiva un hábito pausado."""
    return _transition_route(habit_id, service, "resume")


@router.post("/{habit_id}/archive", response_model=HabitOut)
def archive_habit(habit_id: str, service: HabitService = Depends(_service)):
    """Archiva un hábito (operación preferida frente a eliminar)."""
    return _transition_route(habit_id, service, "archive")


@router.post("/{habit_id}/restore", response_model=HabitOut)
def restore_habit(habit_id: str, service: HabitService = Depends(_service)):
    """Restaura un hábito archivado a activo."""
    return _transition_route(habit_id, service, "restore")


@router.delete("/{habit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_habit(habit_id: str, service: HabitService = Depends(_service)):
    """Elimina físicamente un hábito solo si no tiene registros."""
    success = service.delete(habit_id)
    if not success:
        if service.get(habit_id) is None:
            raise HTTPException(status_code=404, detail="Hábito no encontrado")
        raise HTTPException(
            status_code=409,
            detail=(
                "No se puede eliminar un hábito con registros. "
                "Archívalo en su lugar."
            ),
        )


@router.get("/{habit_id}/calendar")
def habit_calendar(
    habit_id: str,
    month: str,
    service: HabitService = Depends(_service),
):
    """Días de un mes con programación y estado de registro de un hábito."""
    try:
        return service.calendar(habit_id, month)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# --- Registros diarios -----------------------------------------------------


@router.get("/{habit_id}/entries", response_model=list[EntryOut])
def list_entries(
    habit_id: str,
    from_: str | None = Query(default=None, alias="from"),
    to: str | None = None,
    service: HabitService = Depends(_service),
):
    """Historial de registros de un hábito, con rango opcional `from`/`to`."""
    try:
        return service.list_entries(habit_id, from_date=from_, to_date=to)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{habit_id}/entries", response_model=EntryOut, status_code=status.HTTP_201_CREATED)
def create_entry(
    habit_id: str, entry_in: EntryCreate, service: HabitService = Depends(_service)
):
    """Registra un día del hábito (por defecto, el día local actual)."""
    try:
        return service.create_entry(habit_id, entry_in)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/{habit_id}/entries/{entry_date}", response_model=EntryOut)
def update_entry(
    habit_id: str,
    entry_date: str,
    entry_in: EntryUpdate,
    service: HabitService = Depends(_service),
):
    """Corrige el registro de una fecha sin duplicar el historial."""
    try:
        return service.update_entry(habit_id, entry_date, entry_in)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{habit_id}/entries/{entry_date}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(
    habit_id: str, entry_date: str, service: HabitService = Depends(_service)
):
    """Borra un registro: el día vuelve a estar no registrado."""
    success = service.delete_entry(habit_id, entry_date)
    if not success:
        if service.get(habit_id) is None:
            raise HTTPException(status_code=404, detail="Hábito no encontrado")
        raise HTTPException(status_code=404, detail="Registro no encontrado")
