# Handoff: MIND-002 — Primer núcleo funcional de Mind (Spaces, Inbox, Canvas y Cards)

**Fecha:** 22 de noviembre de 2026
**De:** Mimo / Developer
**Para:** Product Owner (aceptación) y Reviewer independiente cuando esté disponible
**Entrega:** MIND-002
**Rama:** `product/mind-core` (base: `3362502`, HEAD remoto de `product/lifeos-evolution`)
**Estado:** REVIEW — no es DONE; la aceptación del PO es explícita.

## Qué se hizo

Primera versión funcional de Mind, local-first y sin IA: el usuario crea contextos
de trabajo (Spaces), captura ideas en un Inbox transversal, crea Canvases y coloca
Cards de texto que conservan contenido y posición al reabrir la aplicación.

- **Navegación:** entrada "Mind" en la barra lateral, rutas `#/mind`, `#/mind/inbox`,
  `#/mind/spaces/:id` y `#/mind/canvases/:id`. Las rutas existentes quedan intactas.
- **Spaces:** crear (nombre obligatorio, descripción opcional), listar, renombrar,
  archivar y restaurar. Sin jerarquía de carpetas y sin borrado físico.
- **Inbox único:** un solo Inbox por instalación, reservado y no editable desde la UI.
  La unicidad está garantizada por un índice único parcial en la base y por un
  bootstrap idempotente en el servicio.
- **Captura rápida:** crea una Note canónica y su membresía en el Inbox; se consulta
  y edita con el API canónico de Notas. Los errores de guardado conservan el borrador.
- **Canvases:** crear, listar, abrir, renombrar, editar descripción, archivar y restaurar.
- **Cards:** Note canónica + instancia visual con posición del mundo, tamaño inicial y
  orden; edición del texto con el API de Notas; movimiento con drag o teclado;
  quitar la Card no borra la Note; eliminar la Note elimina sus referencias Mind.
- **Espacial:** pan, zoom (rueda, botones, pellizco y teclado) y alternativa por teclado
  para mover Cards. La posición se guarda al terminar la interacción, no por frame.
- **Datos:** backup y exportación JSON incluyen las tablas de Mind, con IDs y referencias
  preservados.

Fuera de alcance, sin infraestructura preparatoria: Orbes, IA, voz, documentos por
bloques, multimedia, relaciones semánticas y conexiones entre Cards (MIND-003/004).

## Decisión técnica (SPEC §3)

| Pregunta | Respuesta |
|---|---|
| ¿Cómo se garantiza el Inbox único? | `mind_spaces.is_inbox` con índice único parcial (`is_inbox = 1`); `MindService.ensure_inbox()` lo crea de forma idempotente en cada petición de Mind, con savepoint para no perder la transacción. |
| ¿Cómo es una Card sin duplicar Notes? | La Card es una fila de `mind_canvas_nodes` (posición/tamaño/orden) que referencia `notes.id`. El texto vive solo en `notes`. |
| ¿Qué pasa si se elimina una Note? | `ON DELETE CASCADE` en `mind_space_notes` y `mind_canvas_nodes`: desaparecen membresías y representaciones visuales, sin huérfanos. Quitar un nodo no borra la Note. |
| ¿Cómo se exportan y restauran? | Export JSON versionado (se agregaron las 4 tablas de Mind conservando IDs) y backup SQLite consistente; la restauración usa el mecanismo existente, ya probado con datos de Mind. |
| ¿Qué queda para MIND-003/004? | Conexiones entre Cards, relaciones semánticas, grupos avanzados y documentos por bloques: no se creó ninguna tabla ni endpoint para ellos. |

## Qué se verificó

| Verificación | Comando | Resultado |
|---|---|---|
| Pruebas backend | `.venv\Scripts\python.exe -m pytest -q` | ✅ **163 passed** (140 previos + 23 nuevos de MIND-002), sin regresiones |
| Lint | `.venv\Scripts\python.exe -m ruff check app tests` | ✅ All checks passed |
| Sintaxis JS | `node --check` sobre los 10 archivos de `frontend/assets/js` | ✅ OK (incluye `mind.js`, `mind-canvas.js`, `mind-common.js`) |
| Migraciones | `python verify_migrations.py` (base temporal) | ✅ base vacía → `0006_mind`; downgrade/upgrade a `0005` y `0001`; `integrity_check=ok`; `foreign_key_check=0`; índice único parcial rechaza un 2.º Inbox; CASCADE borra las referencias de la Note |
| QA visual | Edge headless vía CDP, sin dependencias nuevas, 4 rutas × 3 viewports (1440×900, 768×1024, 390×844) = 12 capturas | ✅ 0 overflow horizontal, 0 errores de consola, contenido renderizado en las 12 combinaciones |
| QA interactiva | Edge headless vía CDP | ✅ Crear Card desde la UI (3 → 4 Cards), drag persistido en backend (`Posición guardada`, x/y actualizados en la API), movimiento por teclado (+8 px), Inbox y Spaces navegables |

**Entorno de QA:** Uvicorn en `127.0.0.1:8012` con `LIFEOS_DATA_DIR` temporal
(`%TEMP%\opencode\mind-qa`); la base personal nunca se usó. Las capturas quedaron en
`%TEMP%\opencode\mind-qa\shots`.

**Nota de la verificación final (post-publicación del primer commit):** la última
pasada de `ruff check app tests` detectó 2 avisos en `tests/test_mind.py` (bloque de
imports sin ordenar y una variable local asignada sin usar). Se corrigieron en un
commit posterior, sin tocar el comportamiento de las pruebas ni el código de
producción; el árbol final queda con `All checks passed` y `163 passed`.

## Qué queda pendiente

- **Revisión independiente y aceptación del PO** (la entrega queda en REVIEW).
- MIND-003 (Canvas interactivo y relaciones visuales) sigue en PLANNING: no se creó
  ninguna tabla ni endpoint preparatorio para conexiones.
- No hay borrado físico de Spaces ni Canvases: por decisión de SPEC, el archivado es
  la operación preferida. Si el PO quiere borrado físico, requiere SPEC nueva.
- No hay búsqueda ni relaciones semánticas (MIND-005) ni integración con Projects,
  Tasks y Habits (MIND-006).
- QA visual con tema claro: la QA se ejecutó con el tema por defecto (oscuro).

## Comandos ejecutados

```
cd backend
python -m pytest -q                                   → 163 passed
python -m ruff check app tests                        → All checks passed
python verify_migrations.py                           → TODAS LAS VERIFICACIONES PASARON
cd ..
node --check frontend/assets/js/*.js                  → OK en los 10 archivos

# QA (base temporal, nunca la personal)
$env:LIFEOS_DATA_DIR="$env:TEMP\opencode\mind-qa"
$env:LIFEOS_ALLOWED_HOSTS="127.0.0.1:8012,localhost:8012"
python -m alembic upgrade head                        → 0006_mind
python -m uvicorn app.main:app --host 127.0.0.1 --port 8012
node %TEMP%\opencode\mind-qa\qa-mind.mjs              → 12 capturas + interacciones OK
```

## Archivos modificados

| Archivo | Cambios |
|---|---|
| `backend/app/modules/mind/models.py` | Nuevo: `mind_spaces`, `mind_canvases`, `mind_space_notes`, `mind_canvas_nodes` |
| `backend/app/modules/mind/schemas.py` | Nuevo: esquemas Pydantic de Spaces, Canvases, Cards, capturas y nodos |
| `backend/app/modules/mind/repository.py` | Nuevo: acceso a datos de Mind |
| `backend/app/modules/mind/service.py` | Nuevo: reglas de negocio, Inbox idempotente y eventos `mind.*` |
| `backend/app/modules/mind/__init__.py` | Nuevo: API pública del módulo |
| `backend/app/api/v1/mind.py` | Nuevo: rutas `/api/v1/mind/**` |
| `backend/app/main.py` | Router de Mind y handlers 404/409 de dominio |
| `backend/app/modules/data_service.py` | Export JSON: 4 tablas de Mind |
| `backend/migrations/versions/0006_mind.py` | Nueva: migración de las tablas de Mind |
| `backend/verify_migrations.py` | HEAD `0006_mind`, comprobaciones de Mind y downgrade/upgrade |
| `backend/tests/test_mind.py` | Nuevo: 23 pruebas de MIND-002 (criterios 2-11) |
| `frontend/index.html` | Enlace de navegación "Mind" y hoja de estilos `mind.css` |
| `frontend/assets/js/app.js` | Import y rutas de Mind; el enlace "Mind" queda activo en sus subrutas |
| `frontend/assets/js/mind.js` | Nuevo: vista principal, Inbox y detalle de Space |
| `frontend/assets/js/mind-canvas.js` | Nuevo: workspace del Canvas (pan, zoom, drag, edición, guardado) |
| `frontend/assets/js/mind-common.js` | Nuevo: utilidades compartidas (API, estados, modal) |
| `frontend/assets/css/mind.css` | Nuevo: estilos de Mind y del Canvas |
| `DATABASE.md` | Versión 0.5: tablas, integridad, índices, exportación y pruebas de Mind |
| `docs/factory/work/MIND_WORK_QUEUE.md` | MIND-002 → REVIEW |
| `docs/factory/work/MIND-002/HANDOFF.md` | Este documento |
| `docs/product/MIND_*.md`, `docs/factory/work/MIND-002/SPEC.md`, `docs/factory/work/MIND_WORK_QUEUE.md` | Documentos aprobados transferidos desde `planning/mind-001` (sin fusionar la rama) |

## Decisiones tomadas

1. **El contenido canónico sigue siendo `notes`.** Mind agrega contextos y
   representaciones visuales, no un segundo sistema de notas.
2. **Título de captura derivado.** `notes.title` es obligatorio y no vacío; cuando la
   captura no trae título se usa la primera línea del contenido. Así la captura
   conserva un título estable sin modificar el modelo ni el API de Notas.
3. **Inbox con índice único parcial.** La garantía de unicidad está en la base (no
   solo en la aplicación) y la creación es idempotente en cada petición de Mind.
4. **Archivado en lugar de borrado.** Spaces y Canvases se archivan y se restauran; no
   se implementa borrado físico.
5. **Coordenadas del mundo.** La posición se guarda en coordenadas del lienzo, no del
   viewport: el mismo Canvas se abre igual en distintas pantallas y con distinto zoom.
6. **Guardado al terminar la interacción.** El drag persiste una sola vez al soltar;
   el movimiento por teclado usa debounce. Nunca se persiste por frame.
7. **Zoom con mínimo legible.** "Ajustar" no baja del 50 %: por debajo el texto deja
   de ser legible y el resto del lienzo se alcanza desplazando.
8. **Sin infraestructura futura.** No hay tablas de conexiones, relaciones semánticas,
   documentos por bloques ni sesiones de Orbe.

## Contexto para la siguiente tarea

- La rama `product/mind-core` se creó desde `origin/product/lifeos-evolution` (`3362502`)
  y quedó con upstream apuntando a esa rama remota: **publicar con
  `git push -u origin product/mind-core`** para no escribir en Evolution.
- Durante la implementación, `origin/product/lifeos-evolution` avanzó 4 commits
  (`a3b5a08`: home, notas, formularios progresivos y responsive). **Ninguno de esos
  commits toca los archivos modificados por MIND-002** (`main.py`, `data_service.py`,
  `verify_migrations.py`, `frontend/index.html`, `frontend/assets/js/app.js`,
  `DATABASE.md`), por lo que la sincronización posterior de la rama no debería
  generar conflictos. La base acordada de esta entrega se mantuvo en `3362502`.
- El worktree de Evolution (`LifeOS`) conserva trabajo sin publicar ajeno
  (`home.js`, `app.css`, `contexto_lifeos.txt`, `UX-01/02/03`): no se tocó.
- El esquema de Mind ya está en `0006_mind`; las siguientes tareas de Mind deben
  encadenar su migración sobre `down_revision = "0006_mind"`.
- Los endpoints `POST /mind/canvases/{id}/nodes` (representar una Note existente) y
  `GET/PATCH /mind/spaces` ya existen para MIND-003, pero **la UI todavía no ofrece
  mover notas entre Canvases ni arrastrar desde el Inbox**.

## Estado de la cola de trabajo

- `MIND-001`: REVIEW (roadmap 0.2 consolidado).
- `MIND-002`: **REVIEW** — este handoff.
- `MIND-003` en adelante: PLANNING; requieren SPEC y aceptación del PO.
