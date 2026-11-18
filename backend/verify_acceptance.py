"""Verificación de aceptación de extremo a extremo (Fase 6).

Recorre, contra un servidor Uvicorn real y una base temporal:
  1. instalacion limpia (alembic upgrade head desde base vacia);
  2. primer inicio y Health check;
  3. frontend estatico servido desde el mismo origen;
  4. flujos criticos por API (proyecto, tarea, widgets, tema, export);
  5. cierre y reinicio del servidor;
  6. persistencia de datos y preferencias tras el reinicio.

Nunca usa la base personal: LIFEOS_DATA_DIR apunta a un directorio temporal
(AGENTS.md seccion 5). Uso:  .venv\\Scripts\\python.exe verify_acceptance.py
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

PORT = 8017
BASE = f"http://127.0.0.1:{PORT}"
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = tempfile.mkdtemp(prefix="lifeos_accept_")
LOG_PATH = os.path.join(DATA_DIR, "uvicorn.log")

ENV = {
    **os.environ,
    "LIFEOS_DATA_DIR": DATA_DIR,
    "LIFEOS_ALLOWED_HOSTS": f"127.0.0.1:{PORT},localhost:{PORT}",
}

failures = []


def check(label, ok, detail=""):
    status = "OK  " if ok else "FAIL"
    print(f"[{status}] {label}" + (f" -- {detail}" if detail and not ok else ""))
    if not ok:
        failures.append(label)


def http(method, path, body=None, content_type="application/json"):
    """Minimal HTTP client: returns (status, bytes)."""
    data = None
    if body is not None:
        data = body if isinstance(body, bytes) else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(BASE + path, data=data, method=method)
    req.add_header("Host", f"127.0.0.1:{PORT}")
    if data is not None:
        req.add_header("Content-Type", content_type)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def start_server():
    log = open(LOG_PATH, "ab")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app",
         "--host", "127.0.0.1", "--port", str(PORT), "--log-level", "warning"],
        cwd=BACKEND_DIR,
        env=ENV,
        stdout=log,
        stderr=log,
    )
    for _ in range(60):
        try:
            status, _body = http("GET", "/api/v1/health")
            if status == 200:
                return proc
        except (urllib.error.URLError, ConnectionError, TimeoutError, OSError):
            pass
        time.sleep(0.5)
    proc.terminate()
    raise RuntimeError("el servidor no respondio; ver %s" % LOG_PATH)


def stop_server(proc):
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=10)


def main():
    print(f"Directorio temporal de datos: {DATA_DIR}")

    # 1. Instalacion limpia: migraciones desde base vacia
    mig = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR, env=ENV, capture_output=True, text=True, timeout=120,
    )
    check("instalacion limpia: alembic upgrade head", mig.returncode == 0,
          (mig.stdout + mig.stderr)[-500:])

    # 2. Primer inicio
    proc = start_server()
    try:
        status, body = http("GET", "/api/v1/health")
        health = json.loads(body)
        check("primer inicio: /api/v1/health", status == 200 and health.get("status") == "ok")

        # 3. Frontend en el mismo origen
        status, body = http("GET", "/")
        check("frontend: Home responde 200", status == 200 and b"<html" in body.lower())
        status, _body = http("GET", "/assets/css/app.css")
        check("frontend: CSS estatico", status == 200)
        status, _body = http("GET", "/assets/js/app.js")
        check("frontend: JS estatico", status == 200)

        # Host no permitido rechazado (SECURITY.md)
        req = urllib.request.Request(BASE + "/api/v1/health")
        req.add_header("Host", "ejemplo-malo.test")
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                bad_host_status = resp.status
        except urllib.error.HTTPError as exc:
            bad_host_status = exc.code
        check("seguridad: Host no permitido -> 400", bad_host_status == 400)

        # 4. Flujos criticos
        status, body = http("POST", "/api/v1/projects",
                            {"name": "Proyecto aceptacion", "status": "active"})
        project = json.loads(body) if status in (200, 201) else {}
        check("crear proyecto", status == 201, body[:200])

        status, body = http("POST", "/api/v1/tasks",
                            {"title": "Tarea aceptacion", "status": "pending",
                             "project_id": project.get("id")})
        task = json.loads(body) if status in (200, 201) else {}
        check("crear tarea vinculada", status == 201, body[:200])

        status, body = http("GET", "/api/v1/dashboard/widgets")
        widgets = json.loads(body) if status == 200 else []
        check("dashboard: 6 widgets (Fase 6 + 7)",
              status == 200 and len(widgets) == 6, str(len(widgets)))

        status, _body = http("PUT", "/api/v1/settings/theme", {"theme": "dark"})
        check("guardar tema oscuro", status == 200)

        # 4b. Flujos de habitos (Fase 7)
        status, body = http("POST", "/api/v1/habits",
                            {"name": "Habito aceptacion", "start_date": "2026-01-01",
                             "frequency_type": "daily"})
        habit = json.loads(body) if status in (200, 201) else {}
        check("crear habito", status == 201, body[:200])

        status, body = http("POST", f"/api/v1/habits/{habit.get('id')}/entries",
                            {"entry_date": "2026-01-02"})
        entry = json.loads(body) if status in (200, 201) else {}
        check("registrar dia del habito", status == 201 and
              entry.get("status") == "completed", body[:200])

        status, body = http("GET", "/api/v1/habits/today")
        today = json.loads(body) if status == 200 else []
        check("vista hoy de habitos", status == 200 and isinstance(today, list))

        status, body = http("GET", "/api/v1/habits/stats")
        stats = json.loads(body) if status == 200 else []
        check("metricas de habitos",
              status == 200 and len(stats) >= 1
              and "current_streak" in stats[0], body[:200])

        status, body = http("GET", "/api/v1/habits/week")
        week = json.loads(body) if status == 200 else {}
        check("vista semanal de habitos",
              status == 200 and len(week.get("items", [])) >= 1, body[:200])

        status, body = http("GET", "/api/v1/export")
        export = json.loads(body) if status == 200 else {}
        check("exportacion JSON versionada",
              status == 200 and export.get("format_version") == 1
              and len(export.get("projects", [])) >= 1
              and len(export.get("tasks", [])) >= 1
              and len(export.get("habits", [])) >= 1
              and len(export.get("habit_entries", [])) >= 1)

        task_id = task.get("id")
        project_id = project.get("id")
    finally:
        # 5. Cierre
        stop_server(proc)
        print("[OK  ] servidor detenido (cierre)")

    # 6. Reinicio y persistencia
    proc = start_server()
    try:
        status, body = http("GET", "/api/v1/tasks")
        tasks = json.loads(body) if status == 200 else []
        titles = [t.get("title") for t in tasks]
        check("reinicio: la tarea persiste", "Tarea aceptacion" in titles, str(titles))

        status, body = http("GET", f"/api/v1/projects/{project_id}")
        check("reinicio: el proyecto persiste",
              status == 200 and json.loads(body).get("name") == "Proyecto aceptacion")

        status, body = http("GET", "/api/v1/settings/theme")
        check("reinicio: la preferencia de tema persiste",
              status == 200 and json.loads(body).get("theme") == "dark", body[:200])

        status, body = http("GET", f"/api/v1/tasks/{task_id}")
        check("reinicio: la tarea se puede consultar por id", status == 200)

        status, body = http("GET", f"/api/v1/habits/{habit.get('id')}")
        check("reinicio: el habito persiste",
              status == 200 and json.loads(body).get("name") == "Habito aceptacion",
              body[:200])
    finally:
        stop_server(proc)
        print("[OK  ] servidor detenido (reinicio completado)")

    print()
    if failures:
        print(f"FALLAS: {len(failures)}")
        for item in failures:
            print(f"  - {item}")
        return 1
    print("TODAS LAS VERIFICACIONES DE ACEPTACION PASARON")
    return 0


if __name__ == "__main__":
    try:
        code = main()
    finally:
        shutil.rmtree(DATA_DIR, ignore_errors=True)
    sys.exit(code)
