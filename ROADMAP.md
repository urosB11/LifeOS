# Life OS — Roadmap de desarrollo

**Estado:** Fases 1–7 completadas (MVP 0.1 aceptado + Habit Tracker 0.2); siguientes fases pendientes de autorización
**Versión:** 0.2
**Fecha:** 18 de noviembre de 2026
**Relacionado con:** `VISION.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md`, `DATABASE.md`, `SECURITY.md` y `AGENTS.md`

> El roadmap define orden y criterios de salida, no fechas. Cada fase entrega una porción ejecutable, integrada y probada. Autorizar una fase no autoriza automáticamente todas las siguientes.

## 1. Objetivo

Construir un núcleo útil y confiable antes de ampliar Life OS con nuevos módulos, IA, agentes o integraciones. El MVP 0.1 se limita a Home, Tasks, Projects, Notes, Settings básicos, widgets internos, persistencia, exportación/backup y métricas sencillas.

## 2. Reglas de ejecución

1. Avanzar por tareas pequeñas y demostrables.
2. Priorizar flujos verticales completos frente a capas vacías.
3. Probar las reglas de datos al implementarlas, no al final.
4. Usar bases temporales para pruebas; nunca la base personal.
5. Actualizar documentación afectada junto al cambio.
6. No ampliar alcance por sugerencia de una skill, plugin o agente.
7. Antes de modificar un modelo o política aprobada, explicar el impacto y proponer actualización documental.
8. No hacer push, publicar, desplegar ni exponer servicios sin autorización explícita.

## 3. Estado de planificación — Fase 0 cerrada

Se adoptan las siguientes decisiones para iniciar el MVP:

- monolito modular con frontend HTML/CSS/JavaScript nativo y backend FastAPI;
- FastAPI sirve el frontend estático y la API en el mismo origen;
- SQLite + SQLAlchemy 2.x síncrono + Alembic;
- Python 3.11+, Uvicorn, pytest, HTTPX y Ruff;
- UUIDv4 en texto, timestamps UTC y vencimientos `YYYY-MM-DD` locales;
- tareas `pending/completed`, prioridades opcionales `low/normal/high`;
- proyectos `active/completed/archived`; archivado preferido y borrado físico restringido si hay tareas;
- notas muchos-a-muchos con proyectos y tareas; etiquetas reutilizables y normalizadas;
- widgets `upcoming_tasks`, `active_projects`, `quick_add_task`, `quick_add_note`;
- exportación JSON completa; backup/restauración SQLite documentados y probados;
- servidor en `127.0.0.1:8000`, sin login, CORS abierto ni exposición remota;
- Context7 para documentación de desarrollo; Anthropic `frontend-design` y la skill oficial `fastapi` como apoyo externo de implementación.

La especificación visual, las rutas de archivos, los requisitos y los modelos de datos están documentados. La Fase 0 se considera cerrada; las decisiones futuras de nube, autenticación remota e IA no bloquean el MVP.

## 4. Fases de desarrollo

### Fase 1 — Fundaciones ejecutables

**Objetivo:** crear un esqueleto local que arranque y pueda verificarse de forma repetible.

**Trabajo:**
- inicializar repositorio, `.gitignore`, README y estructura mínima;
- preparar entorno Python y dependencias en `pyproject.toml`;
- configurar FastAPI/Uvicorn en `127.0.0.1:8000`;
- servir una primera página estática desde FastAPI en el mismo origen;
- añadir `/api/v1/health` y manejo básico de errores;
- configurar SQLAlchemy/Alembic y una base SQLite de desarrollo vacía;
- habilitar claves foráneas y verificar conexión;
- configurar pytest/HTTPX y Ruff;
- separar datos locales y backups del repositorio.

**Entregables:** app local ejecutable, página inicial, health check, entorno repetible y tests iniciales.

**Salida:** arranque/apagado documentado; servidor escucha solo en loopback; una prueba API pasa; datos locales quedan fuera de Git; no hay módulos funcionales prematuros.

### Fase 2 — Proyectos y tareas

**Objetivo:** entregar el primer flujo de dominio completo.

**Trabajo:**
- modelos, esquemas, repositorios, servicios y rutas de proyectos/tareas;
- migración inicial y restricciones de integridad;
- CRUD de tareas, completar/reabrir, prioridad, vencimiento y filtros;
- CRUD de proyectos, estados, archivado/restauración y borrado restringido;
- relación tarea-proyecto;
- eventos dentro de la transacción;
- interfaz mínima para listar, crear, editar y consultar proyectos/tareas;
- tests unitarios, API e integración.

**Entregables:** proyectos y tareas usables desde interfaz y API, persistentes y probados.

**Salida:** las operaciones exigidas pasan; las referencias inválidas se rechazan; los eventos no quedan desincronizados; borrar proyecto con tareas falla de forma segura.

### Fase 3 — Notas, relaciones y etiquetas

**Objetivo:** incorporar notas reutilizables y conectadas sin obligar a clasificarlas.

**Trabajo:**
- CRUD de notas de texto y búsqueda simple;
- relaciones muchos-a-muchos con proyectos y tareas;
- etiquetas compartidas con normalización Unicode/case-insensitive;
- asignar, quitar y filtrar etiquetas;
- mostrar notas relacionadas desde proyectos y tareas;
- definir comportamiento de eliminación según `DATABASE.md`;
- integrar UI mínima y pruebas completas de integridad.

**Entregables:** notas, vínculos y etiquetas funcionales con migraciones y pruebas.

**Salida:** una nota puede estar sola o tener múltiples relaciones; las notas sobreviven al borrado de tareas/proyectos; los duplicados de etiquetas se impiden.

### Fase 4 — Home, dashboard configurable y Settings

**Objetivo:** integrar los módulos en una interfaz coherente.

**Trabajo:**
- navegación Home, Tasks, Projects, Notes y Settings;
- dashboard con los cuatro widgets del catálogo;
- controles accesibles para mostrar/ocultar/reordenar;
- persistir preferencias de widgets;
- tema claro/oscuro/sistema y zona horaria;
- responsive, accesibilidad, estados de carga/vacío/error;
- revisión visual con `frontend-design` y skill local de UI.

**Entregables:** interfaz integrada, responsive y personalizable.

**Salida:** flujos principales utilizables en escritorio y móvil; widget prefs persisten; datos reflejados sin duplicación.

### Fase 5 — Exportación, backup, restauración y métricas

**Objetivo:** asegurar conservación y recuperación de información y entregar análisis básico verificable.

**Trabajo:**
- exportación JSON versionada incluyendo relaciones, etiquetas y preferencias;
- backup SQLite consistente y procedimiento de restauración;
- pruebas de backup/restore en base temporal;
- métricas básicas de tareas y proyectos con fórmulas documentadas;
- revisión de seguridad, logs, host local, validaciones y repositorio;
- documentar recuperación y límites de privacidad.

**Entregables:** exportación, recuperación y resúmenes básicos probados.

**Salida:** JSON conserva relaciones; backup se restaura; métricas coinciden con casos calculados manualmente; los controles de seguridad pasan.

### Fase 6 — Estabilización y aceptación del MVP

**Objetivo:** validar Life OS como aplicación integrada.

**Trabajo:**
- recorrer todos los escenarios de `REQUIREMENTS.md`;
- probar instalación limpia, primer inicio, cierre y reinicio;
- probar migraciones desde base vacía y una versión previa de prueba;
- revisar errores funcionales, accesibilidad y responsive;
- corregir antes pérdida/corrupción de datos, exposición y fallos de flujos críticos;
- completar README, guía de usuario, documentación de recuperación y changelog;
- presentar resultados y limitaciones antes de etiquetar versión.

**Entregables:** MVP 0.1 probado y documentado, lista de limitaciones y backlog.

**Salida:** todos los criterios de aceptación pasan; no quedan defectos críticos; instalación, uso y recuperación pueden repetirse.

### Fase 7 — Habit Tracker (Life OS 0.2)

**Objetivo:** entregar seguimiento de hábitos diarios con registros, métricas verificables y widgets, sin gamificación ni notificaciones.

**Trabajo:**
- modelos `habits` y `habit_entries` con migración `0005_habits`, `UNIQUE(habit_id, entry_date)`, índices y `ON DELETE RESTRICT`;
- modalidades binaria y cuantificable (`target_value`/`target_unit`); frecuencias `daily` y `weekly_days` con días 0=lunes … 6=domingo; sin motor de recurrencias;
- CRUD de hábitos con validación de configuración sobre estado fusionado y transiciones `pause/resume/archive/restore` idempotentes (inválidas → 409);
- borrado físico solo sin registros; archivar como operación preferida;
- registro diario: un registro por día programado y no futuro, corrección con PATCH sin duplicar historial y borrado que devuelve el día a no registrado;
- vista de hoy, calendario mensual y vista semanal con la regla de días programados en backend;
- métricas (racha actual, mejor racha, cumplimiento semanal/mensual y consistencia) según `DATABASE.md` sección 8.1, con “Sin datos” cuando el denominador es cero;
- widgets `habits_today` y `habits_week` visibles por defecto y resumen de hábitos en `/analytics/summary`;
- `habits` y `habit_entries` en exportación JSON y respaldo;
- eventos `habit.*` con metadatos sin nombres ni contenido;
- pruebas de CRUD, validaciones, transiciones, registros, métricas con datos sintéticos, widgets y export; verificación de aceptación end-to-end.

**Entregables:** hábitos usables desde interfaz y API, métricas verificadas y documentación actualizada.

**Salida:** se cumplen FR-HAB-01 a FR-HAB-15; las métricas coinciden con conjuntos sintéticos conocidos; no hay pérdida de datos; las funciones esenciales operan offline.

## 5. Backlog posterior al MVP

Orden tentativo, revisable según uso real:

1. Agenda y objetivos (los hábitos se entregaron en la Fase 7).
2. Work: CV, portfolio, vacantes, postulaciones y entrevistas.
3. Business: clientes, proyectos comerciales, ventas e ingresos.
4. Finance: cuentas, movimientos, presupuestos y reportes específicos.
5. Analytics transversal avanzado: períodos, filtros, tendencias, comparaciones y objetivos.
6. AI Orchestrator con herramientas tipadas, permisos mínimos y aprobación de acciones sensibles.
7. Integraciones (Gmail, Calendar, Telegram, GitHub), sincronización y alojamiento remoto con diseño de seguridad específico.
8. App Center ampliado con procedencia, permisos y aislamiento; nunca ejecución arbitraria no revisada.

## 6. Priorización de defectos

1. pérdida o corrupción de datos;
2. vulnerabilidades o exposición no autorizada;
3. violaciones de integridad o permisos;
4. bloqueos de flujos principales;
5. accesibilidad, responsive y usabilidad;
6. mejoras estéticas menores.

## 7. Definition of Done

Cada tarea queda terminada cuando:

- cumple un requisito o criterio identificable;
- el cambio es acotado y coherente con arquitectura/seguridad;
- incluye pruebas apropiadas y pasan realmente;
- se revisó el diff y no hay secretos, datos ni archivos accidentales;
- se actualizó la documentación afectada;
- el agente informa archivos, comportamiento, comandos ejecutados, resultados y limitaciones.

## 8. Regla de avance

Cada fase se ejecuta con autorización explícica del usuario; completar una fase no autoriza automáticamente la siguiente. OpenCode comienza inspeccionando el directorio, comprobando el entorno, proponiendo un plan para la fase y trabajando en incrementos pequeños sin sobrescribir archivos del usuario.
