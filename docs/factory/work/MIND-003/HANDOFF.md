# Handoff — MIND-003: Canvas interactivo y relaciones visuales

**Fecha:** 23 de noviembre de 2026
**Estado:** PLANNING — SPEC consolidada para revisión; no READY
**Rama:** `planning/mind-001`
**Base de documentación:** `1fa1033914f80e92374b9bb820bc544a09f361d3`
**Archivos de esta entrega:** `SPEC.md`, `HANDOFF.md`

## Resultado

Se redactó [SPEC.md](./SPEC.md) con alcance, arquitectura, persistencia, conexiones visuales, multi-selección, resize, orden, accesibilidad, touch, undo/redo, exportación, backup, restauración, migraciones, pruebas y criterios de aceptación.

MIND-003 sigue en PLANNING. No se actualizó la cola porque ya refleja ese estado. No se implementó código, no se creó ni aplicó una migración, no se usó ninguna base de datos y no se tocó Evolution.

## Revisiones Opus y Sonnet

Los informes no estaban disponibles en el commit remoto ni en los documentos locales revisados. La guía del PO especifica qué debe entregar cada revisor, pero no incluye sus resultados. No se atribuye ninguna conclusión a Opus o Sonnet.

- **Falta Opus:** revisión read-only de flujo UX de conectar/seleccionar/redimensionar, complejidad, criterios observables y valor de frames.
- **Falta Sonnet:** auditoría read-only de modelo/API real, constraints para conexiones del mismo Canvas, diseño de undo/redo persistente, borrado de Notes, export/backup/restore y migración.
- **Gate:** solicitar e integrar ambos informes, resolver sus observaciones o registrar decisiones explícitas y obtener aceptación del PO. Hasta entonces, no pasar a READY ni implementar.

La SPEC formula un diseño consistente con las decisiones disponibles, pero no reemplaza esas revisiones independientes.

## Decisiones consolidadas

1. Una conexión es una línea no dirigida, sin tipo, etiqueta ni significado de dominio, entre dos Cards del mismo Canvas. Las relaciones semánticas quedan en MIND-005.
2. Notes sigue siendo el contenido canónico. Añadir una Note existente representa el mismo ID en el Canvas y conserva su membresía del Inbox; no hay movimiento silencioso ni duplicación.
3. Se reutilizan las columnas `width`, `height` y `z_index` de `mind_canvas_nodes`; no se propone duplicar el estado de tamaño/orden.
4. La selección múltiple es temporal, no una entidad persistida. Mover una selección es una única acción atómica. Frames y grupos persistentes quedan fuera.
5. Undo/redo se limita a acciones del Canvas, persiste en SQLite, se acota a 100 operaciones por Canvas y no es event sourcing. Editar el contenido de una Note sigue siendo responsabilidad de Notes.
6. La eliminación canónica de Note sigue siendo destructiva y confirmada; invalida historial solo en los Canvases afectados para impedir que se restauren referencias muertas.
7. Home no recibe widgets de Mind ni comparte su grid/motor. No se incluyen Cards vivas de Tasks/Projects/Habits, Knowledge, documentos, IA ni MIND-005.
8. La SPEC no elige números de revisión Alembic: la colisión `0006_mind` / `0006_home_widget_grid` requiere decisión de integración antes de implementar.

## Estado Git y trabajo local preservado

Antes de cambiar archivos se verificaron rama, HEAD, status y worktrees:

- **Evolution** (`LifeOS`): `product/lifeos-evolution`, HEAD `bcc3db7`; permanecen sin tocar los untracked `contexto_lifeos.txt`, `docs/factory/work/UX-01/`, `UX-02/` y `UX-03/`.
- **Planificación** (`LifeOS-mind-planning`): `planning/mind-001`, HEAD `66f06b7`, limpio y siete commits detrás. Se actualizó la referencia con `git fetch` y se hizo únicamente fast-forward hasta `1fa1033`; no había cambios locales que descartar.
- **Implementación Mind** (`LifeOS-mind-implementation`): `product/mind-core`, HEAD `ffbf3a7`, con cambios locales preexistentes que permanecen intactos.

El worktree de implementación contiene un borrador/trabajo MIND-003A sin publicar: cambios en API, modelos, repositorio, schemas, servicio, exportación, pruebas y verificación de migraciones; `0006_mind.py` aparece eliminado localmente; `0007_mind.py`, `0008_mind_canvas_edges.py`, `ADR-005-mind-edges-frames.md` y `MIND-003A/` aparecen como untracked. Se preservó todo y no se copió ni adoptó en esta SPEC. En particular, los tipos de edge, Frames, campos IA-ready y el alcance de integración de ese borrador no sustituyen las decisiones de producto vigentes.

## Riesgos y pendientes de diseño

- Recibir la revisión de Sonnet para validar historial persistente, referencias normalizadas, invalidación al borrar Notes y las constraints de conexiones entre nodos del mismo Canvas.
- Recibir la revisión de Opus para confirmar lasso/touch, acciones accesibles de conexión, límites de resize y si Frames aportan valor; el alcance actual los excluye.
- Resolver la estrategia Alembic de integración mediante decisión del PO. No renumerar ni crear migraciones durante la planificación.
- Al implementar, verificar otra vez el estado de los tres worktrees y reconciliar conscientemente el trabajo local MIND-003A antes de escribir en `product/mind-core`.
- Confirmar en prueba temporal la versión actual del export y mantener compatibilidad con paquetes previos.

## QA documental

- Contraste con D1–D5, límites Home/Mind, `MIND_PRODUCT_MODEL.md`, `MIND_ROADMAP.md`, guía PO, SPEC MIND-002 y HANDOFF MIND-002.
- La definición mantiene separadas conexión visual y relación semántica; no agrega Notes, Knowledge ni entidades canónicas duplicadas.
- Los requisitos de persistencia, historial, integridad, export/restore, migración y pruebas se describen sin afirmar que se ejecutaron.
- No se corrieron pytest, Ruff, `node --check`, smoke ni pruebas de base: el cambio es documentación de planificación.
