"""Tests de Hábitos — CRUD, validaciones, transiciones y borrado (Fase 7)."""


def _create_habit(client, **overrides):
    payload = {
        "name": "Leer 20 minutos",
        "start_date": "2026-11-01",
        **overrides,
    }
    return client.post("/api/v1/habits", json=payload)


# --- CRUD y validaciones -------------------------------------------------


def test_create_habit_defaults(client):
    r = _create_habit(client)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["status"] == "active"
    assert data["frequency_type"] == "daily"
    assert data["frequency_days"] is None
    assert data["target_value"] is None
    assert data["position"] == 0


def test_create_habit_weekly_days_roundtrip(client):
    r = _create_habit(client, frequency_type="weekly_days", frequency_days=[0, 2, 4])
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["frequency_days"] == [0, 2, 4]

    # Persiste como JSON y se devuelve como lista
    r = client.get(f"/api/v1/habits/{data['id']}")
    assert r.status_code == 200
    assert r.json()["frequency_days"] == [0, 2, 4]


def test_create_habit_quantifiable(client):
    r = _create_habit(
        client,
        name="Correr",
        target_value=5.0,
        target_unit="km",
        color="#267568",
        category="Salud",
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["target_value"] == 5.0
    assert data["target_unit"] == "km"
    assert data["color"] == "#267568"
    assert data["category"] == "Salud"


def test_create_habit_empty_name_rejected(client):
    assert _create_habit(client, name="   ").status_code == 422


def test_create_habit_invalid_date_rejected(client):
    assert _create_habit(client, start_date="no-es-fecha").status_code == 422


def test_create_habit_invalid_color_rejected(client):
    assert _create_habit(client, color="rojo").status_code == 422


def test_create_habit_weekly_without_days_rejected(client):
    r = _create_habit(client, frequency_type="weekly_days", frequency_days=None)
    assert r.status_code == 400, r.text
    assert "frequency_days" in r.json()["detail"]


def test_create_habit_invalid_frequency_rejected(client):
    r = _create_habit(client, frequency_type="cada_3_dias")
    assert r.status_code == 400, r.text


def test_create_habit_invalid_day_rejected(client):
    r = _create_habit(client, frequency_type="weekly_days", frequency_days=[0, 9])
    assert r.status_code == 400, r.text


def test_create_habit_duplicate_days_rejected(client):
    r = _create_habit(client, frequency_type="weekly_days", frequency_days=[1, 1])
    assert r.status_code == 400, r.text


def test_create_habit_unit_without_target_rejected(client):
    r = _create_habit(client, target_unit="km")
    assert r.status_code == 400, r.text
    assert "target_value" in r.json()["detail"]


def test_create_habit_negative_target_rejected(client):
    r = _create_habit(client, target_value=-1, target_unit="km")
    assert r.status_code == 422, r.text


def test_position_auto_assigned(client):
    _create_habit(client, name="Primero")
    r = _create_habit(client, name="Segundo")
    assert r.json()["position"] == 1
    r = _create_habit(client, name="Tercero", position=0)
    assert r.json()["position"] == 0


def test_list_habits_filters(client):
    _create_habit(client, name="Diario", category="Salud")
    _create_habit(
        client, name="Lunes", category="Estudio",
        frequency_type="weekly_days", frequency_days=[0],
    )
    r = client.get("/api/v1/habits")
    assert len(r.json()) == 2
    assert [h["name"] for h in r.json()] == ["Diario", "Lunes"]  # orden por posición

    r = client.get("/api/v1/habits?category=Estudio")
    assert [h["name"] for h in r.json()] == ["Lunes"]

    r = client.get("/api/v1/habits?status=archived")
    assert r.json() == []


def test_get_habit_not_found(client):
    assert client.get("/api/v1/habits/nope").status_code == 404


def test_update_habit(client):
    habit_id = _create_habit(client).json()["id"]
    r = client.patch(
        f"/api/v1/habits/{habit_id}", json={"name": "Leer 30 minutos", "category": "Mind"}
    )
    assert r.status_code == 200, r.text
    assert r.json()["name"] == "Leer 30 minutos"
    assert r.json()["category"] == "Mind"


def test_update_habit_merged_frequency_validation(client):
    """La validación cruzada usa el estado fusionado, no el payload parcial."""
    habit_id = _create_habit(client).json()["id"]

    # Pasar a weekly_days sin días → inválido (los días actuales son NULL)
    r = client.patch(f"/api/v1/habits/{habit_id}", json={"frequency_type": "weekly_days"})
    assert r.status_code == 400, r.text

    # Primero fijar los días y luego el tipo, en payloads separados: ok
    r = client.patch(f"/api/v1/habits/{habit_id}", json={"frequency_days": [1, 3]})
    assert r.status_code == 200, r.text
    r = client.patch(f"/api/v1/habits/{habit_id}", json={"frequency_type": "weekly_days"})
    assert r.status_code == 200, r.text
    assert r.json()["frequency_days"] == [1, 3]


def test_update_habit_not_found(client):
    assert client.patch("/api/v1/habits/nope", json={"name": "x"}).status_code == 404


# --- Transiciones de estado ----------------------------------------------


def test_pause_resume_cycle(client):
    habit_id = _create_habit(client).json()["id"]

    r = client.post(f"/api/v1/habits/{habit_id}/pause")
    assert r.status_code == 200 and r.json()["status"] == "paused"

    # Idempotente: pausar ya pausado no falla
    r = client.post(f"/api/v1/habits/{habit_id}/pause")
    assert r.status_code == 200 and r.json()["status"] == "paused"

    r = client.post(f"/api/v1/habits/{habit_id}/resume")
    assert r.status_code == 200 and r.json()["status"] == "active"


def test_archive_and_restore(client):
    habit_id = _create_habit(client).json()["id"]

    r = client.post(f"/api/v1/habits/{habit_id}/archive")
    assert r.status_code == 200 and r.json()["status"] == "archived"

    # Archivado: no se puede pausar ni reactivar
    assert client.post(f"/api/v1/habits/{habit_id}/pause").status_code == 409
    assert client.post(f"/api/v1/habits/{habit_id}/resume").status_code == 409

    r = client.post(f"/api/v1/habits/{habit_id}/restore")
    assert r.status_code == 200 and r.json()["status"] == "active"


def test_transitions_not_found(client):
    for action in ("pause", "resume", "archive", "restore"):
        assert client.post(f"/api/v1/habits/nope/{action}").status_code == 404


def test_pause_active_habit_from_archived_rejected(client):
    habit_id = _create_habit(client).json()["id"]
    client.post(f"/api/v1/habits/{habit_id}/archive")
    assert client.post(f"/api/v1/habits/{habit_id}/pause").status_code == 409


# --- Borrado -------------------------------------------------------------


def test_delete_habit_without_entries(client):
    habit_id = _create_habit(client).json()["id"]
    r = client.delete(f"/api/v1/habits/{habit_id}")
    assert r.status_code == 204
    assert client.get(f"/api/v1/habits/{habit_id}").status_code == 404


def test_delete_habit_with_entries_rejected(client, db):
    """ON DELETE RESTRICT: un hábito con registros no se elimina (se archiva)."""
    from app.modules.habits.models import HabitEntry

    habit_id = _create_habit(client).json()["id"]
    db.add(HabitEntry(habit_id=habit_id, entry_date="2026-11-18", status="completed"))
    db.flush()

    r = client.delete(f"/api/v1/habits/{habit_id}")
    assert r.status_code == 409, r.text
    assert client.get(f"/api/v1/habits/{habit_id}").status_code == 200


def test_delete_habit_not_found(client):
    assert client.delete("/api/v1/habits/nope").status_code == 404


# --- Eventos --------------------------------------------------------------


def test_habit_events_recorded(client, db):
    """El cambio de dominio y su evento se confirman juntos (DATABASE.md §6)."""
    from app.db.activity import ActivityEvent
    from sqlalchemy import select

    habit_id = _create_habit(client).json()["id"]
    client.post(f"/api/v1/habits/{habit_id}/pause")

    events = list(
        db.execute(
            select(ActivityEvent).where(ActivityEvent.entity_id == habit_id)
        ).scalars()
    )
    types = [e.event_type for e in events]
    assert "habit.created" in types
    assert "habit.status_changed" in types
    status_event = next(e for e in events if e.event_type == "habit.status_changed")
    assert '"from": "active"' in status_event.metadata_json
    assert '"to": "paused"' in status_event.metadata_json
    # Nunca contenido sensible en metadatos
    assert "Leer 20 minutos" not in status_event.metadata_json


# --- Registros diarios (entries) ------------------------------------------


def _today(db):
    from app.core.clock import local_today

    return local_today(db)


def test_create_entry_defaults_to_today(client, db):
    habit_id = _create_habit(client).json()["id"]
    r = client.post(f"/api/v1/habits/{habit_id}/entries", json={})
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["entry_date"] == _today(db).isoformat()
    assert data["status"] == "completed"  # registro rápido binario


def test_create_entry_past_date(client):
    habit_id = _create_habit(client, start_date="2026-01-01").json()["id"]
    r = client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": "2026-01-05", "status": "skipped"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["status"] == "skipped"


def test_create_entry_future_rejected(client, db):
    from datetime import timedelta

    habit_id = _create_habit(client).json()["id"]
    future = (_today(db) + timedelta(days=1)).isoformat()
    r = client.post(f"/api/v1/habits/{habit_id}/entries", json={"entry_date": future})
    assert r.status_code == 400, r.text
    assert "futuro" in r.json()["detail"]


def test_create_entry_unscheduled_day_rejected(client):
    # Frecuencia solo lunes (0); 2026-11-17 es martes
    habit_id = _create_habit(
        client, frequency_type="weekly_days", frequency_days=[0],
        start_date="2026-01-01",
    ).json()["id"]
    r = client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": "2026-11-17"},
    )
    assert r.status_code == 400, r.text
    assert "programado" in r.json()["detail"]


def test_create_entry_before_start_date_rejected(client):
    habit_id = _create_habit(client, start_date="2026-06-01").json()["id"]
    r = client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": "2026-05-31"},
    )
    assert r.status_code == 400, r.text


def test_create_entry_duplicate_rejected_then_patch_corrects(client):
    habit_id = _create_habit(client, start_date="2026-01-01").json()["id"]
    r = client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": "2026-01-05"},
    )
    assert r.status_code == 201, r.text
    entry_id = r.json()["id"]

    r = client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": "2026-01-05"},
    )
    assert r.status_code == 409, r.text

    # Corregir: el historial no se duplica
    r = client.patch(
        f"/api/v1/habits/{habit_id}/entries/2026-01-05",
        json={"status": "skipped", "note": "enfermo"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["id"] == entry_id
    assert r.json()["status"] == "skipped"

    entries = client.get(f"/api/v1/habits/{habit_id}/entries").json()
    assert len(entries) == 1


def test_quantifiable_entry_derives_status(client):
    habit_id = _create_habit(
        client, target_value=5.0, target_unit="km", start_date="2026-01-01"
    ).json()["id"]

    r = client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": "2026-01-05", "value": 3.0},
    )
    assert r.json()["status"] == "pending"

    r = client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": "2026-01-06", "value": 5.5},
    )
    assert r.json()["status"] == "completed"


def test_binary_entry_rejects_value(client):
    habit_id = _create_habit(client, start_date="2026-01-01").json()["id"]
    r = client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": "2026-01-05", "value": 2},
    )
    assert r.status_code == 400, r.text
    assert "binario" in r.json()["detail"]


def test_entry_not_found(client):
    habit_id = _create_habit(client).json()["id"]
    r = client.patch(
        f"/api/v1/habits/{habit_id}/entries/2026-01-05", json={"status": "completed"}
    )
    assert r.status_code == 404
    r = client.delete(f"/api/v1/habits/{habit_id}/entries/2026-01-05")
    assert r.status_code == 404


def test_entry_habit_not_found(client):
    r = client.post("/api/v1/habits/nope/entries", json={})
    assert r.status_code == 404
    r = client.get("/api/v1/habits/nope/entries")
    assert r.status_code == 404


def test_list_entries_range(client):
    habit_id = _create_habit(client, start_date="2026-01-01").json()["id"]
    for d in ("2026-01-05", "2026-01-06", "2026-01-07"):
        client.post(f"/api/v1/habits/{habit_id}/entries", json={"entry_date": d})

    entries = client.get(f"/api/v1/habits/{habit_id}/entries").json()
    assert [e["entry_date"] for e in entries] == [
        "2026-01-05", "2026-01-06", "2026-01-07",
    ]

    entries = client.get(
        f"/api/v1/habits/{habit_id}/entries?from=2026-01-06&to=2026-01-06"
    ).json()
    assert [e["entry_date"] for e in entries] == ["2026-01-06"]

    r = client.get(f"/api/v1/habits/{habit_id}/entries?from=fecha-mala")
    assert r.status_code == 400
    r = client.get(
        f"/api/v1/habits/{habit_id}/entries?from=2026-01-07&to=2026-01-05"
    )
    assert r.status_code == 400


def test_delete_entry_returns_day_to_unregistered(client):
    habit_id = _create_habit(client, start_date="2026-01-01").json()["id"]
    client.post(
        f"/api/v1/habits/{habit_id}/entries", json={"entry_date": "2026-01-05"}
    )
    r = client.delete(f"/api/v1/habits/{habit_id}/entries/2026-01-05")
    assert r.status_code == 204
    assert client.get(f"/api/v1/habits/{habit_id}/entries").json() == []
    r = client.delete(f"/api/v1/habits/{habit_id}/entries/2026-01-05")
    assert r.status_code == 404


def test_habits_today(client, db):
    """Solo hábitos activos programados para hoy, con su registro."""
    today = _today(db).isoformat()

    daily = _create_habit(client, name="Diario").json()
    _create_habit(
        client, name="Lunes", frequency_type="weekly_days",
        frequency_days=[0], start_date="2026-01-01",
    )
    paused = _create_habit(client, name="Pausado").json()
    client.post(f"/api/v1/habits/{paused['id']}/pause")

    r = client.get("/api/v1/habits/today")
    assert r.status_code == 200
    items = r.json()
    # Solo 'Diario': 'Lunes' no es programado hoy (miércoles) y 'Pausado' está pausado
    assert [i["habit"]["name"] for i in items] == ["Diario"]
    assert items[0]["entry"] is None

    client.post(f"/api/v1/habits/{daily['id']}/entries", json={})
    items = client.get("/api/v1/habits/today").json()
    assert items[0]["entry"] is not None
    assert items[0]["entry"]["entry_date"] == today
    assert items[0]["entry"]["status"] == "completed"

    # Se puede consultar como cualquier otro ID (no hay colisión de rutas)
    assert client.get(f"/api/v1/habits/{daily['id']}").status_code == 200


def test_entry_events_recorded(client, db):
    from app.db.activity import ActivityEvent
    from sqlalchemy import select

    habit_id = _create_habit(client, start_date="2026-01-01").json()["id"]
    client.post(f"/api/v1/habits/{habit_id}/entries", json={"entry_date": "2026-01-05"})
    client.patch(
        f"/api/v1/habits/{habit_id}/entries/2026-01-05", json={"status": "skipped"}
    )

    types = [
        e.event_type
        for e in db.execute(
            select(ActivityEvent).where(ActivityEvent.entity_id == habit_id)
        ).scalars()
    ]
    assert "habit.entry_created" in types
    assert "habit.entry_updated" in types


def test_habit_calendar_month(client):
    """El calendario devuelve programación y registro por día (regla en backend)."""
    habit_id = _create_habit(
        client, frequency_type="weekly_days", frequency_days=[0],
        start_date="2026-11-02",
    ).json()["id"]
    # 2026-11-02 es lunes: primer día programado
    client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": "2026-11-02"},
    )

    r = client.get(f"/api/v1/habits/{habit_id}/calendar?month=2026-11")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["month"] == "2026-11"
    assert data["today"].startswith("2026-11")  # hoy cae en este mes
    assert len(data["days"]) == 30

    by_date = {d["date"]: d for d in data["days"]}
    # Lunes 2: programado y completado
    assert by_date["2026-11-02"]["scheduled"] is True
    assert by_date["2026-11-02"]["entry_status"] == "completed"
    # Martes 3: no programado
    assert by_date["2026-11-03"]["scheduled"] is False
    assert by_date["2026-11-03"]["entry_status"] is None
    # Lunes 9: programado sin registro
    assert by_date["2026-11-09"]["scheduled"] is True
    assert by_date["2026-11-09"]["entry_status"] is None
    # Antes de start_date: no programado
    assert by_date["2026-11-01"]["scheduled"] is False

    # Mes inválido
    r = client.get(f"/api/v1/habits/{habit_id}/calendar?month=2026-13")
    assert r.status_code == 400
    r = client.get(f"/api/v1/habits/{habit_id}/calendar?month=nada")
    assert r.status_code == 400
    # Hábito inexistente
    r = client.get("/api/v1/habits/nope/calendar?month=2026-11")
    assert r.status_code == 404


# --- Métricas y rachas (DATABASE.md 8.1) ---------------------------------


def _days_ago(db, n):
    from datetime import timedelta

    return (_today(db) - timedelta(days=n)).isoformat()


def _stats(client, habit_id=None):
    url = "/api/v1/habits/stats"
    if habit_id:
        url += f"?habit_id={habit_id}"
    r = client.get(url)
    assert r.status_code == 200, r.text
    return r.json()


def test_stats_current_streak_counts_back(client, db):
    """Racha actual = días programados consecutivos completados que terminan hoy."""
    habit_id = _create_habit(client, start_date=_days_ago(db, 10)).json()["id"]
    for n in (0, 1, 2):  # hoy, ayer y antes de ayer
        client.post(
            f"/api/v1/habits/{habit_id}/entries",
            json={"entry_date": _days_ago(db, n)},
        )
    stats = _stats(client, habit_id)[0]
    assert stats["current_streak"] == 3
    assert stats["best_streak"] == 3


def test_stats_streak_zero_when_today_missing(client, db):
    """Si hoy está programado y no está completado, la racha es 0."""
    habit_id = _create_habit(client, start_date=_days_ago(db, 5)).json()["id"]
    for n in (1, 2):  # ayer y antes de ayer completados, hoy sin registro
        client.post(
            f"/api/v1/habits/{habit_id}/entries",
            json={"entry_date": _days_ago(db, n)},
        )
    stats = _stats(client, habit_id)[0]
    assert stats["current_streak"] == 0
    # Pero la mejor racha conserva el pasado
    assert stats["best_streak"] == 2


def test_stats_skipped_breaks_streak(client, db):
    habit_id = _create_habit(client, start_date=_days_ago(db, 5)).json()["id"]
    client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": _days_ago(db, 0)},
    )
    client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": _days_ago(db, 1), "status": "skipped"},
    )
    stats = _stats(client, habit_id)[0]
    assert stats["current_streak"] == 1  # hoy completado; ayer omitido corta


def test_stats_unscheduled_days_do_not_break_streak(client, db):
    """Los días no programados no interrumpen la racha (DATABASE.md 8.1)."""
    from datetime import timedelta

    today = _today(db)
    # Programado: hoy, ayer y hace 3 días (el día intermedial no programado)
    days = sorted({
        today.weekday(),
        (today - timedelta(days=1)).weekday(),
        (today - timedelta(days=3)).weekday(),
    })
    habit_id = _create_habit(
        client,
        frequency_type="weekly_days",
        frequency_days=days,
        start_date=_days_ago(db, 7),
    ).json()["id"]
    for n in (0, 1):  # hoy y ayer completados
        client.post(
            f"/api/v1/habits/{habit_id}/entries",
            json={"entry_date": _days_ago(db, n)},
        )
    stats = _stats(client, habit_id)[0]
    # El día -2 no está programado: no corta; el día -3 programado sin
    # registro corta => racha 2.
    assert stats["current_streak"] == 2


def test_stats_compliance_week_and_month(client, db):
    """Cumplimiento = completed / programados * 100; hoy sin registrar resta."""
    habit_id = _create_habit(client, start_date=_days_ago(db, 60)).json()["id"]
    # Completa todo desde el inicio hasta ayer; hoy queda pendiente
    for n in range(1, 61):
        client.post(
            f"/api/v1/habits/{habit_id}/entries",
            json={"entry_date": _days_ago(db, n)},
        )
    stats = _stats(client, habit_id)[0]

    sched_week = _today(db).weekday() + 1  # días de la semana actual hasta hoy
    assert stats["scheduled_week"] == sched_week
    assert stats["completed_week"] == sched_week - 1  # hoy sin registrar
    assert stats["weekly_compliance"] == round(
        (sched_week - 1) / sched_week * 100, 1
    )

    sched_month = _today(db).day
    assert stats["scheduled_month"] == sched_month
    assert stats["completed_month"] == sched_month - 1
    assert stats["monthly_compliance"] == round(
        (sched_month - 1) / sched_month * 100, 1
    )


def test_stats_consistency_counts_skipped(client, db):
    """Consistencia incluye skipped en el numerador; cumplimiento no."""
    from datetime import timedelta

    today = _today(db)
    habit_id = _create_habit(client, start_date=today.replace(day=1).isoformat()).json()["id"]

    current = today.replace(day=1)
    while current <= today:
        status = "skipped" if current.day == 1 else "completed"
        client.post(
            f"/api/v1/habits/{habit_id}/entries",
            json={"entry_date": current.isoformat(), "status": status},
        )
        current += timedelta(days=1)

    stats = _stats(client, habit_id)[0]
    n = today.day  # días programados del mes hasta hoy (hábito diario)
    assert stats["scheduled_month"] == n
    assert stats["completed_month"] == n - 1  # un día omitido
    assert stats["monthly_compliance"] == round((n - 1) / n * 100, 1)
    assert stats["consistency_month"] == 100.0  # omitido cuenta como registrado


def test_stats_no_data_shows_none(client, db):
    """Sin días programados en el período => 'Sin datos' (None), no 0 %."""
    habit_id = _create_habit(client, start_date=_days_ago(db, 0)).json()["id"]
    stats = _stats(client, habit_id)[0]
    # Hábito de hoy: la semana sí tiene 1 día programado, pero el mes también
    assert stats["scheduled_month"] >= 1
    # Hábito que empieza en el futuro: ningún período tiene días programados
    future_id = _create_habit(client, name="Futuro", start_date=_days_ago(db, -5)).json()["id"]
    stats = _stats(client, future_id)[0]
    assert stats["scheduled_week"] == 0
    assert stats["weekly_compliance"] is None
    assert stats["monthly_compliance"] is None
    assert stats["consistency_month"] is None
    assert stats["current_streak"] == 0
    assert stats["best_streak"] == 0


def test_stats_best_streak_history(client, db):
    habit_id = _create_habit(client, start_date=_days_ago(db, 30)).json()["id"]
    for n in range(25, 20, -1):  # 5 días consecutivos antiguos (hace 25..21)
        client.post(
            f"/api/v1/habits/{habit_id}/entries",
            json={"entry_date": _days_ago(db, n)},
        )
    for n in (0, 1):  # racha actual de 2
        client.post(
            f"/api/v1/habits/{habit_id}/entries",
            json={"entry_date": _days_ago(db, n)},
        )
    stats = _stats(client, habit_id)[0]
    assert stats["best_streak"] == 5
    assert stats["current_streak"] == 2


def test_stats_global_excludes_archived_and_404(client, db):
    active_id = _create_habit(client, name="Activo").json()["id"]
    archived_id = _create_habit(client, name="Archivado").json()["id"]
    client.post(f"/api/v1/habits/{archived_id}/archive")

    stats = _stats(client)
    ids = [s["habit_id"] for s in stats]
    assert active_id in ids
    assert archived_id not in ids

    # Detalle de un hábito archivado sigue disponible con id explícito
    detail = _stats(client, archived_id)
    assert len(detail) == 1 and detail[0]["name"] == "Archivado"

    r = client.get("/api/v1/habits/stats?habit_id=nope")
    assert r.status_code == 404

    # /stats no colisiona con /habits/{habit_id}
    assert client.get(f"/api/v1/habits/{active_id}").status_code == 200


def test_habits_week_view(client, db):
    """Vista semanal: 7 días lun-dom con programación y registro (widget)."""
    from datetime import date, timedelta

    today = _today(db)
    week_start = today - timedelta(days=today.weekday())

    daily = _create_habit(client, name="Diario", start_date=_days_ago(db, 3)).json()
    client.post(f"/api/v1/habits/{daily['id']}/entries", json={})  # hoy completado
    weekly = _create_habit(
        client,
        name="Solo hoy",
        frequency_type="weekly_days",
        frequency_days=[today.weekday()],
        start_date=_days_ago(db, 30),
    ).json()
    assert weekly["id"]  # creado correctamente
    paused = _create_habit(client, name="Pausado").json()
    client.post(f"/api/v1/habits/{paused['id']}/pause")
    archived = _create_habit(client, name="Archivado").json()
    client.post(f"/api/v1/habits/{archived['id']}/archive")

    r = client.get("/api/v1/habits/week")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["week_start"] == week_start.isoformat()
    assert data["today"] == today.isoformat()

    # Solo no archivados, ordenados por posición
    names = [i["habit"]["name"] for i in data["items"]]
    assert names == ["Diario", "Solo hoy"]

    for item in data["items"]:
        assert len(item["days"]) == 7
        assert item["days"][0]["date"] == week_start.isoformat()

    # Registro de hoy en el hábito diario
    daily_item = next(i for i in data["items"] if i["habit"]["name"] == "Diario")
    by_date = {d["date"]: d for d in daily_item["days"]}
    assert by_date[today.isoformat()]["scheduled"] is True
    assert by_date[today.isoformat()]["entry_status"] == "completed"

    # 'Solo hoy' solo tiene programado el día de hoy esta semana
    weekly_item = next(i for i in data["items"] if i["habit"]["name"] == "Solo hoy")
    for day in weekly_item["days"]:
        expected = date.fromisoformat(day["date"]).weekday() == today.weekday()
        assert day["scheduled"] is expected

    # /week no colisiona con /habits/{habit_id}
    assert client.get(f"/api/v1/habits/{daily['id']}").status_code == 200


def test_week_and_calendar_expose_entry_value(client, db):
    """HAB-002: semana/calendario exponen entry_value (aditivo, sin ruta nueva).

    Cubre registro histórico por debajo/sobre la meta, corrección con PATCH,
    borrado con DELETE y hábito binario (value None). Sin estados nuevos.
    """
    from datetime import timedelta

    today = _today(db)
    past = (today - timedelta(days=2)).isoformat()
    quant = _create_habit(
        client, name="Agua", start_date=_days_ago(db, 10),
        target_value=8.0, target_unit="vasos",
    ).json()

    # Registro histórico por debajo de la meta → pending con valor
    r = client.post(
        f"/api/v1/habits/{quant['id']}/entries",
        json={"entry_date": past, "value": 5.0},
    )
    assert r.status_code == 201, r.text

    # Calendario del mes del registro histórico: estado y valor
    cal = client.get(
        f"/api/v1/habits/{quant['id']}/calendar?month={past[:7]}"
    ).json()
    cal_day = next(d for d in cal["days"] if d["date"] == past)
    assert cal_day["scheduled"] is True
    assert cal_day["entry_status"] == "pending"
    assert cal_day["entry_value"] == 5.0

    # Registro de hoy: la semana expone estado y valor
    r = client.post(
        f"/api/v1/habits/{quant['id']}/entries",
        json={"value": 6.0},
    )
    assert r.status_code == 201, r.text
    week = client.get("/api/v1/habits/week").json()
    item = next(i for i in week["items"] if i["habit"]["id"] == quant["id"])
    by_date = {d["date"]: d for d in item["days"]}
    assert by_date[today.isoformat()]["entry_status"] == "pending"
    assert by_date[today.isoformat()]["entry_value"] == 6.0

    # Corrección histórica con PATCH: supera la meta → completed en calendario
    r = client.patch(
        f"/api/v1/habits/{quant['id']}/entries/{past}",
        json={"value": 9.0},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"
    cal = client.get(
        f"/api/v1/habits/{quant['id']}/calendar?month={past[:7]}"
    ).json()
    cal_day = next(d for d in cal["days"] if d["date"] == past)
    assert cal_day["entry_status"] == "completed"
    assert cal_day["entry_value"] == 9.0

    # DELETE: la semana vuelve a no registrado (ambos campos en None)
    r = client.delete(f"/api/v1/habits/{quant['id']}/entries/{today.isoformat()}")
    assert r.status_code == 204
    week = client.get("/api/v1/habits/week").json()
    item = next(i for i in week["items"] if i["habit"]["id"] == quant["id"])
    day = {d["date"]: d for d in item["days"]}[today.isoformat()]
    assert day["entry_status"] is None
    assert day["entry_value"] is None

    # Hábito binario: registra cumplimiento sin valor → entry_value None
    binary = _create_habit(
        client, name="Binario", start_date=_days_ago(db, 10)
    ).json()
    client.post(
        f"/api/v1/habits/{binary['id']}/entries",
        json={"entry_date": past},
    )
    cal = client.get(
        f"/api/v1/habits/{binary['id']}/calendar?month={past[:7]}"
    ).json()
    cal_day = next(d for d in cal["days"] if d["date"] == past)
    assert cal_day["entry_status"] == "completed"
    assert cal_day["entry_value"] is None

    # Sin estados persistidos nuevos: los status siguen siendo los conocidos
    entries = client.get(f"/api/v1/habits/{quant['id']}/entries").json()
    assert {e["status"] for e in entries} <= {"pending", "completed", "skipped"}


def test_stats_metadata_and_formula_sources(client, db):
    """Transparencia: período, denominadores y fuentes visibles en la respuesta."""
    habit_id = _create_habit(
        client, start_date=_days_ago(db, 10), target_value=5.0, target_unit="km"
    ).json()["id"]
    client.post(
        f"/api/v1/habits/{habit_id}/entries",
        json={"entry_date": _days_ago(db, 0), "value": 6.0},
    )
    stats = _stats(client, habit_id)[0]
    assert stats["today"] == _today(db).isoformat()
    assert stats["week_start"] <= stats["today"]
    assert stats["month"] == _today(db).isoformat()[:7] + "-01"
    assert stats["target_value"] == 5.0
    assert stats["target_unit"] == "km"
    assert stats["completed_month"] == 1  # value 6 >= meta 5 => completed


