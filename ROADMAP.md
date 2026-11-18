# Life OS — Roadmap de desarrollo

**Estado:** planificación aprobada; Fase 0 cerrada y Fase 1 lista para iniciar
**Versión:** 0.2
**Fecha:** 17 de noviembre de 2026
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

## 5. Backlog posterior al MVP

Orden tentativo, revisable según uso real:

1. Agenda, objetivos y hábitos.
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

La autorización actual permite iniciar la Fase 1 en OpenCode. No autoriza a ejecutar todas las fases en una sola corrida. OpenCode debe comenzar inspeccionando el directorio, comprobar el entorno, proponer un plan para Fase 1 y luego trabajar en incrementos pequeños sin sobrescribir archivos del usuario.
