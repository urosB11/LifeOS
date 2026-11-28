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

## QA visual tema claro (2026-11-22 — verificación complementaria)

SPEC MIND-002 §5 exige QA "en temas disponibles"; la primera pasada solo cubrió el
tema oscuro por defecto. Se ejecutó una segunda QA forzando `body.theme-light` en
Edge headless vía CDP, sin dependencias nuevas.

| Verificación | Comando | Resultado |
|---|---|---|
| Migraciones en DB temporal nueva | `alembic upgrade head` (LIFEOS_DATA_DIR=`%TEMP%\opencode\mind-qa-light`) | ✅ `0001` → `0006_mind` |
| QA visual tema claro | `node qa-mind-light.mjs` (puerto 8013, Edge headless CDP) | ✅ **13 capturas** (4 rutas × 3 viewports + 1 interacción) |
| Overflow horizontal | 12 combinaciones (1440×900, 768×1024, 390×844) | ✅ **0 overflow**, 0 elementos desbordados |
| Errores de consola | 12 combinaciones | ✅ **0 errores** (0 exceptions, 0 console.error) |
| Contenido renderizado | 12 combinaciones | ✅ Spaces, Inbox, Canvases y Cards visibles en los 12 estados |
| Contraste y legibilidad | Inspección visual de capturas | ✅ Texto oscuro sobre fondo claro, botones verdes con contraste AA, grid sutil visible |
| Interacción tema claro | Crear Card (3 → 4), drag persistido (x=300, y=260), teclado (+8 px) | ✅ `Posición guardada`; movimiento por teclado verificado |

**Entorno de QA:** Uvicorn en `127.0.0.1:8013` con `LIFEOS_DATA_DIR` temporal
(`%TEMP%\opencode\mind-qa-light`); la base personal nunca se usó. Las capturas quedaron en
`%TEMP%\opencode\mind-qa-light\shots`.

**Conclusión:** MIND-002 cumple SPEC §5 en ambos temas disponibles. Sin hallazgos
críticos en tema claro; contraste AA y foco visible verificados visualmente.

## Comandos ejecutados

```
# Verificación de tests (re-ejecutada 2026-11-22)
cd backend
python -m pytest tests/test_mind.py -q               → 23 passed
python -m pytest -q                                   → 163 passed (sin regresiones)
python -m ruff check app tests                        → All checks passed
python verify_migrations.py                           → TODAS LAS VERIFICACIONES PASARON
cd ..
node --check frontend/assets/js/*.js                  → OK en los 11 archivos

# QA tema oscuro (base temporal, nunca la personal)
$env:LIFEOS_DATA_DIR="$env:TEMP\opencode\mind-qa"
$env:LIFEOS_ALLOWED_HOSTS="127.0.0.1:8012,localhost:8012"
python -m alembic upgrade head                        → 0006_mind
python -m uvicorn app.main:app --host 127.0.0.1 --port 8012
node %TEMP%\opencode\mind-qa\qa-mind.mjs              → 12 capturas + interacciones OK

# QA tema claro (2026-11-22 — verificación complementaria SPEC §5)
$env:LIFEOS_DATA_DIR="$env:TEMP\opencode\mind-qa-light"
$env:LIFEOS_ALLOWED_HOSTS="127.0.0.1:8013,localhost:8013"
python -m alembic upgrade head                        → 0001 → 0006_mind
python -m uvicorn app.main:app --host 127.0.0.1 --port 8013
node %TEMP%\opencode\mind-qa-light\seed.mjs          → datos sembrados
node %TEMP%\opencode\mind-qa-light\qa-mind-light.mjs → 13 capturas + interacciones OK
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

### Decisión sobre endpoints fuera del alcance visual de MIND-002

Los endpoints `POST /mind/canvases/{id}/nodes` (representar Note existente en Canvas)
y `GET/PATCH /mind/spaces` están implementados y probados, pero la UI de MIND-002 no
ofrece "arrastrar desde Inbox a Canvas" ni "añadir Note existente" (eso es MIND-003).

**Decisión:** los endpoints quedan **expuestos y probados** en MIND-002. Justificación:
- SPEC MIND-002 §2.5 permite "reutilizar Notes existente si la auditoría confirma que
  cubre los requisitos sin duplicar el modelo" — la implementación lo hace correctamente.
- `attach_note` es la base de MIND-003 (mover notas entre Canvases); tenerlo listo y
  probado reduce el trabajo de la siguiente fase.
- La UI no los expone aún, por lo que no hay riesgo de confusión para el usuario.
- **Alternativa (más estricta):** ocultar/eliminar hasta MIND-003 — no recomendada
  porque duplicaría trabajo y el SPEC no lo exige.

## Contexto para la siguiente tarea

- La rama `product/mind-core` se creó desde `origin/product/lifeos-evolution` (`3362502`)
  y quedó con upstream apuntando a esa rama remota: **publicar con
  `git push -u origin product/mind-core`** para no escribir en Evolution.
- Durante la implementación, `origin/product/lifeos-evolution` avanzó 5 commits
  (`a3b5a08` y `18e1d3c`: home, notas, formularios progresivos, responsive y grid de
  widgets). La base acordada de esta entrega se mantuvo en `3362502`.
- El worktree de Evolution (`LifeOS`) conserva trabajo sin publicar ajeno
  (`contexto_lifeos.txt`, `UX-01/02/03`): no se tocó.
- El esquema de Mind ya está en `0006_mind`; las siguientes tareas de Mind deben
  encadenar su migración sobre `down_revision = "0006_mind"`.
- Los endpoints `POST /mind/canvases/{id}/nodes` (representar una Note existente) y
  `GET/PATCH /mind/spaces` ya existen para MIND-003, pero **la UI todavía no ofrece
  mover notas entre Canvases ni arrastrar desde el Inbox**.

## Riesgos de integración con `product/lifeos-evolution` (sin resolver)

Estos puntos aparecen porque Evolution avanzó durante el trabajo. **No se tocaron**:
resolverlos implica decidir la estrategia de merge, que corresponde al PO.

1. **Colisión de cabeza de Alembic (bloqueante).** Evolution creó
   `0006_home_widget_grid` con `down_revision = "0005_habits"`; Mind creó
   `0006_mind` con el mismo `down_revision`. Al integrar ambas ramas Alembic verá
   **dos cabezas**. Hace falta renumerar una de las dos migraciones (por ejemplo,
   `0007_mind` sobre `0006_home_widget_grid`) o añadir una revisión de merge.
2. **Versión del formato de exportación.** En esta rama el JSON mantiene
   `EXPORT_FORMAT_VERSION = 1` porque las 4 tablas de Mind son aditivas; Evolution
   subió a `2` por los `column_span`/`row_span` de widgets. Tras integrar, la forma
   exportada incluye ambos cambios: corresponde usar `2` (la decisión de Evolution)
   y documentar que la v2 incluye además las tablas de Mind.
3. **`verify_migrations.py` y `DATABASE.md`.** Ambas ramas los modificaron
   (`verify_migrations.py` fija el HEAD esperado y la lista de tablas;
   `DATABASE.md` documenta el esquema). El merge exige reconciliarlos a mano:
   el HEAD debe ser el que resulte de la renumeración del punto 1 y el documento
   debe describir tanto el grid de widgets como las tablas de Mind.

### Estrategia de resolución propuesta (pendiente de aprobación PO)

| Opción | Descripción | Ventajas | Desventajas |
|---|---|---|---|
| **A (recomendada)** | Renumerar `0006_mind` → `0007_mind` con `down_revision = "0006_home_widget_grid"`. | Historial lineal; `verify_migrations.py` solo necesita actualizar HEAD a `0007_mind`; sin migración de merge. | Requiere editar el archivo de migración existente (cambio menor). |
| **B** | Mantener ambas `0006_*` y crear `0007_merge_mind_widgets` con `down_revision` dual. | No toca migraciones existentes. | Historial más complejo; `verify_migrations.py` debe cubrir 3 pasos. |

**Recomendación:** Opción A — más limpia y coherente con el patrón lineal de Alembic
ya usado en `0001`–`0005`. El cambio es solo de metadatos (`revision`, `down_revision`)
sin afectar el contenido de las tablas.

**Nota:** Este plan no ejecuta la renumeración; queda documentado para que el PO
autorice la estrategia antes de cualquier merge a Evolution.

## Estado de la cola de trabajo

- `MIND-001`: REVIEW (roadmap 0.2 consolidado).
- `MIND-002`: **REVIEW** — este handoff.
- `MIND-003` en adelante: PLANNING; requieren SPEC y aceptación del PO.

## Reparación de esquema Mind `0010` (2026-11-27)

**Estado:** REVIEW local, sin commit ni push (instrucción expresa del PO). **Base real no modificada.**

### Problema

La base personal estaba sellada en `0008_mind_canvas_history`, pero su estructura física era anterior al merge `64a3ba4` (los IDs de revisión se reutilizaron). Síntomas reproducidos:

- `OperationalError: no such column: mind_canvas_history.sequence`;
- `IntegrityError: NOT NULL constraint failed: mind_canvas_edges.edge_type`;
- `mind_canvas_nodes` sin el índice único `uq_mind_canvas_nodes_canvas_id_id`.

`alembic upgrade head` directo fallaba en `0006_home_widget_grid` porque `column_span`/`row_span` ya existían.

### Alcance ejecutado (Scope A)

| Archivo | Cambio |
|---|---|
| `backend/migrations/versions/0010_repair_mind_canvas_schema.py` | Repara `mind_canvas_history`, `mind_canvas_edges` y el índice único de nodos. Inspecciona y valida antes de cualquier DDL; aborta ante datos ambiguos. `downgrade()` es no-op documentado. |
| `backend/backup_db.py` | Backup con `sqlite3.Connection.backup` (incluye WAL confirmado), verificación de integridad/FKs/conteos/versión y SHA-256. Rechaza destinos dentro del repo, existentes o iguales al origen. |
| `backend/verify_migrations.py` | HEAD `0010`; escenarios de preservación, abortos, idempotencia, multi-stamp híbrido y backup WAL. |
| `DATABASE.md` | Sección 10.1 con procedimiento, rollback por backup y drift residual. |

No se reconstruyó `mind_canvas_nodes` ni se eliminó `mind_canvas_frame_members`. No se modificaron las migraciones `0006`–`0009`.

### Verificación ejecutada

| Verificación | Comando | Resultado |
|---|---|---|
| Tests backend | `python -m pytest -q` (con `LIFEOS_ALLOWED_HOSTS=127.0.0.1:8000,localhost:8000`) | **186 passed** |
| Ruff de archivos nuevos/modificados | `python -m ruff check backup_db.py verify_migrations.py migrations/versions/0010_repair_mind_canvas_schema.py` | **All checks passed** |
| Suite de migraciones | `python verify_migrations.py` | **Todas las verificaciones pasaron** (incluye multi-stamp híbrido y backup WAL) |
| `alembic check` en base temporal limpia | `alembic check` | **No new upgrade operations detected** |

**Ruff global:** `ruff check .` sigue reportando 44 avisos preexistentes en archivos no tocados por esta reparación (migraciones `0001`–`0009`, `app/api/v1/mind.py`, `app/modules/mind/*`, tests). No se corrigieron para no ampliar el alcance ni modificar migraciones prohibidas.

### Ensayo sobre copia aislada de la base real

Procedimiento ejecutado en `%TEMP%`, nunca sobre `%LOCALAPPDATA%\LifeOS\lifeos.db`:

1. `backup_db.py` creó y verificó una copia (20 tablas, 107 filas, `integrity_check=ok`, 0 violaciones FK, versión `0008`).
2. `alembic stamp 0006_home_widget_grid 0008_mind_canvas_history`.
3. `alembic upgrade head`: solo ejecutó `0009_merge_evolution_mind` y `0010_repair_mind_canvas_schema`.
4. Verificación pre/post: mismas tablas y conteos, datos idénticos en todas las tablas no reconstruidas, history/edges vacíos, columnas/índices/FKs/CHECKs finales, `integrity_check=ok`, `foreign_key_check=0`, `alembic_version=0010`.
5. Smoke HTTP con `TestClient` sobre la copia: Spaces, Canvases y Nodes existentes; `GET /history` sin error; creación de Space/Canvas/Cards/Edge; undo/redo; movimiento espacial persistido; export JSON con tablas Mind.

**Drift residual esperado:** `alembic check` sobre la copia reparada sigue detectando las columnas legacy de `mind_canvas_nodes` y la tabla `mind_canvas_frame_members`. Es Scope A; requiere una migración posterior aprobada.

### Pendiente

- **Aplicación a la base real:** requiere autorización explícita del PO. No se ejecutó `stamp`, `upgrade` ni ninguna escritura sobre la base personal.
- **Commit y push:** pendientes por instrucción expresa; el trabajo está solo en el árbol local de `product/mind-core`.
- **Revisión independiente:** no disponible; la verificación anterior es QA propia.
- QA visual manual de Canvas: no repetida en esta reparación; el smoke HTTP cubre el comportamiento funcional.
