# Life OS — Arquitectura de software

**Estado:** línea base técnica para el MVP 0.1
**Versión:** 0.2
**Fecha:** 17 de noviembre de 2026
**Relacionado con:** `VISION.md`, `REQUIREMENTS.md`, `DATABASE.md`, `SECURITY.md`, `ROADMAP.md` y `AGENTS.md`

> Este documento define la arquitectura inicial aprobada. La prioridad es un monolito modular local, entendible y fácil de probar. No se deben introducir capas o tecnologías adicionales sin una necesidad demostrable.

## 1. Objetivo y restricciones

Life OS se implementará primero como una aplicación web local de un solo usuario. Debe funcionar en hardware modesto, conservar datos sin depender de Internet y permitir una evolución gradual a módulos adicionales.

Restricciones principales:

- presupuesto de infraestructura inicial: cero;
- equipo de desarrollo modesto: 8 GB de RAM;
- funciones esenciales locales y sin IA;
- formatos de datos portables y exportables;
- no exponer la aplicación a la red local o Internet en el MVP;
- minimizar herramientas, dependencias y procesos residentes.

## 2. Decisiones arquitectónicas

| Área | Decisión del MVP | Motivo |
|---|---|---|
| Estilo | Monolito modular | Menos complejidad operativa y despliegue sencillo. |
| Frontend | HTML, CSS y JavaScript nativo | No requiere framework ni proceso de build. |
| Backend | Python 3.11+ y FastAPI | API clara, tipado y validación. |
| API | REST versionada bajo `/api/v1` | Contrato explícito entre frontend y backend. |
| Base | SQLite | Persistencia local sin servidor independiente. |
| ORM | SQLAlchemy 2.x, modo síncrono | Encapsula SQL y relaciones; síncrono reduce complejidad con SQLite. |
| Migraciones | Alembic | Cambios de esquema versionados y repetibles. |
| Servidor | Uvicorn | Ejecuta FastAPI localmente. |
| Pruebas | pytest + HTTPX | Pruebas unitarias, API e integración. |
| Calidad | Ruff | Formato y linting Python si se configura desde el inicio. |
| Git | Repositorio local, GitHub opcional | Historial y recuperación del código sin subir datos personales. |
| Agente | OpenCode | Asistencia para implementar por tareas. |
| Documentación externa | Context7 opcional para desarrollo | Consultar APIs actuales; no participa en ejecución de Life OS. |

No se utilizarán React, Vue, Next.js, Tailwind, Docker, Redis, Celery, Kubernetes, microservicios ni modelos locales en el MVP.

## 3. Vista de alto nivel

```text
Navegador
   │ mismo origen HTTP local
   ▼
FastAPI / Uvicorn (127.0.0.1)
   ├── frontend estático (HTML/CSS/JS)
   └── API REST /api/v1
          │
          ▼
     Servicios de aplicación
          │
          ├── Tasks
          ├── Projects
          ├── Notes + Tags
          ├── Dashboard / Widgets
          └── Analytics básico
          │
          ▼
     Repositorios / SQLAlchemy
          │
          ▼
        SQLite
          └── Activity Events (historial complementario)
```

El frontend se sirve desde FastAPI y consume la API en el mismo origen. Así evitamos CORS y un segundo proceso de servidor durante el MVP. La interfaz no contiene reglas críticas de negocio ni accede directamente a SQLite.

## 4. Capas y responsabilidades

### 4.1 Frontend

- HTML semántico para estructura y accesibilidad.
- CSS con variables para color, tipografía, espaciado, radios y estados.
- JavaScript nativo organizado en módulos ES.
- Consume exclusivamente la API pública `/api/v1`.
- Gestiona estado de presentación, navegación, formularios y mensajes.
- No calcula reglas críticas ni duplica la persistencia.
- No ejecuta contenido HTML proveniente de notas o datos del usuario.

### 4.2 API

- Define rutas, esquemas de entrada/salida y códigos HTTP.
- Valida parámetros y datos recibidos.
- Llama a servicios de aplicación.
- No contiene lógica de negocio extensa ni consultas SQL dispersas.
- Mantiene contrato estable bajo `/api/v1`.

### 4.3 Servicios de aplicación / dominio

- Implementan casos de uso y reglas de negocio.
- Coordinan transacciones.
- Validan relaciones y políticas de borrado/archivado.
- Registran los eventos de actividad correspondientes en la misma transacción.
- No dependen de FastAPI ni de componentes visuales.

### 4.4 Persistencia

- SQLAlchemy 2.x encapsula sesiones, modelos y consultas.
- Alembic gestiona migraciones.
- SQLite conserva la fuente de verdad.
- Las claves foráneas deben estar activadas en cada conexión.
- La dependencia `get_db` es la frontera de transacción de cada request: confirma (`commit`) cuando la ruta termina correctamente y revierte si falla, de modo que el cambio de dominio y su evento se persisten juntos (DATABASE.md §6) y una request fallida no deja escrituras parciales.
- No se accede a la base de datos desde JavaScript ni desde widgets.

### 4.5 Dirección visual y layout inicial

La interfaz tendrá una dirección **calma, técnica y editorial**: debe sentirse como un centro de operaciones personal, no como una landing page de marketing ni como un panel financiero genérico. Priorizar jerarquía, lectura rápida, densidad útil y controles discretos.

- **Paleta base:** fondo general gris cálido muy claro (`#F5F7F6`), superficies blancas (`#FFFFFF`), texto principal grafito (`#1F2926`), texto secundario gris (`#66736E`), bordes suaves (`#E1E7E4`).
- **Acento:** verde petróleo sobrio (`#267568`) para acción primaria, selección y progreso; no usarlo como fondo de grandes superficies.
- **Estados:** ámbar apagado para advertencia, rojo sobrio para error y verde para éxito. El color nunca será la única forma de comunicar un estado.
- **Tema oscuro:** se define mediante tokens equivalentes y mantiene el mismo contraste/jerarquía; no es una paleta independiente que cambie significado.
- **Tipografía:** stack local del sistema (`Segoe UI`, `Aptos`, `system-ui`, sans-serif) en MVP para no depender de descargas ni fuentes remotas. La identidad se consigue mediante escala, peso, interlineado y espaciado, no por cargar muchas fuentes.
- **Escritorio (≥ 1024 px):** navegación lateral persistente de aproximadamente 224 px; cabecera compacta; contenido principal centrado con ancho máximo cercano a 1440 px; dashboard en grilla de dos columnas con separación de 16–20 px.
- **Tablet (768–1023 px):** navegación lateral compacta o colapsable; widgets en una o dos columnas según el ancho disponible.
- **Móvil (< 768 px):** navegación compacta en cabecera o menú accesible; widgets en una columna; padding lateral de 16 px; acciones táctiles con objetivos de al menos 44 × 44 CSS px.
- **Componentes:** tarjetas con bordes discretos y radios moderados; títulos de sección claros; botones primarios reservados a la acción principal; acciones secundarias con estilo neutro; no usar tarjetas para envolver cada línea de texto sin necesidad.
- **Movimiento:** transiciones breves y funcionales (aprox. 120–180 ms); respetar `prefers-reduced-motion` y evitar animación decorativa continua.
- **Accesibilidad:** contraste objetivo WCAG AA para texto normal, foco de teclado visible, estructura semántica, etiquetas de formulario y mensajes asociados a errores.
- **Estados obligatorios:** loading, vacío, error, éxito, selección/foco y confirmación de acciones destructivas.

La skill Anthropic `frontend-design` puede proponer refinamientos, pero cualquier propuesta debe respetar esta dirección, el funcionamiento offline, el stack nativo y los criterios de accesibilidad. La paleta se implementará como variables CSS para permitir ajustes posteriores sin reestructurar componentes.

## 5. Módulos funcionales del MVP

| Módulo | Responsabilidad |
|---|---|
| Home | Síntesis y dashboard; no es fuente de verdad. |
| Tasks | CRUD, estados, prioridades, vencimientos y vínculo opcional a proyecto. |
| Projects | CRUD, estados activo/completado/archivado y consulta de tareas/notas relacionadas. |
| Notes | CRUD, búsqueda simple, vínculos opcionales con múltiples proyectos/tareas y etiquetas. |
| Hábitos | CRUD con frecuencias, registro diario por día programado, calendario/semana y métricas de racha y cumplimiento. |
| Settings | Tema, zona horaria y preferencias básicas del dashboard. |
| Dashboard / Widgets | Catálogo interno, visibilidad, orden y datos derivados de otros módulos. |
| Analytics básico | Consultas deterministas de tareas, proyectos y hábitos; sin LLM ni tablas de agregados. |

Work, Business, Finance, Mind, App Center ampliado y AI Orchestrator se mantienen como áreas futuras. No se crearán módulos vacíos o tablas preparatorias para ellas.

## 6. Dashboard y sistema de widgets

- El catálogo de widgets se define en código y usa IDs estables.
- El MVP incluye `upcoming_tasks`, `active_projects`, `quick_add_task`, `quick_add_note`, `habits_today` y `habits_week`.
- La base almacena visibilidad y posición, no código ejecutable.
- Los widgets consultan servicios o endpoints existentes.
- Los errores de un widget no deben impedir renderizar el resto del dashboard.
- El usuario puede reordenarlos con controles de teclado y mouse accesibles; drag-and-drop queda fuera del primer alcance.
- `config_json` solo se usa cuando un widget tenga opciones reales y validadas.
- No ejecutar plugins dinámicos ni código descargado.

## 7. Modelo de datos e historial

El modelo detallado y las políticas de integridad están en `DATABASE.md`. Entidades del MVP:

- `projects`, `tasks`, `notes`;
- `note_project_links`, `note_task_links`;
- `tags`, `note_tags`;
- `habits`, `habit_entries`;
- `widget_preferences`, `user_preferences`;
- `activity_events`.

Las notas pueden ser independientes o relacionarse con cero o varios proyectos/tareas. Las etiquetas se comparten y no se duplican por diferencias de mayúsculas o espacios. Borrar un proyecto o tarea no borra notas: solo elimina las filas de vínculo correspondientes.

`activity_events` conserva cambios relevantes para métricas futuras. No se implementa event sourcing: las tablas de dominio siguen siendo la fuente de verdad. Los eventos se escriben en la misma transacción que el cambio y nunca contienen el cuerpo completo de una nota, credenciales ni contenido sensible.

## 8. Analytics

Analytics es transversal por diseño, pero su primera implementación es deliberadamente pequeña:

- cantidad de tareas pendientes, completadas y vencidas;
- cantidad de proyectos activos;
- avance de tareas por proyecto;
- hábitos activos, programados hoy, completados hoy, omitidos hoy y pendientes hoy.

Se calculan desde datos operativos y fechas locales; no se almacenan agregados duplicados. Cada métrica debe documentar fórmula, fuente, fecha/período y tratamiento de datos faltantes. El historial de eventos deja preparada la evolución temporal sin construir todavía un almacén analítico.

## 9. Contrato API orientativo

Prefijo: `/api/v1`.

| Recurso | Operaciones iniciales |
|---|---|
| `/health` | Estado básico del proceso y base de datos. |
| `/tasks` | GET, POST; `/tasks/{id}` GET, PATCH, DELETE; completar/reabrir mediante operación de estado explícita. |
| `/projects` | GET, POST; `/projects/{id}` GET, PATCH, DELETE restringido; archivar/restaurar/cambiar estado. |
| `/notes` | GET con búsqueda, filtro por etiqueta, `project_id` o `task_id`, POST; `/notes/{id}` GET, PATCH, DELETE. |
| `/notes/{id}/projects` | Consultar y modificar relaciones con proyectos. |
| `/notes/{id}/tasks` | Consultar y modificar relaciones con tareas. |
| `/tags` | Listar y crear etiquetas reutilizables. |
| `/notes/{id}/tags` | Consultar, asignar y quitar etiquetas. |
| `/habits` | GET con filtro de estado/categoría, POST; `/habits/{id}` GET, PATCH, DELETE restringido; `/habits/{id}/pause|resume|archive|restore`. |
| `/habits/today` | Hábitos activos programados para hoy con su registro. |
| `/habits/week` | Semana local (lunes-domingo) con programación y registro por hábito. |
| `/habits/stats` | Rachas y cumplimiento de un hábito (`habit_id`) o de todos los no archivados. |
| `/habits/{id}/entries` | GET historial con rango `from`/`to`, POST nuevo registro; `/habits/{id}/entries/{fecha}` PATCH y DELETE. |
| `/habits/{id}/calendar` | Días de un mes (`YYYY-MM`) con programación y registro. |
| `/dashboard/widgets` | Consultar catálogo y guardar preferencias de visibilidad/orden. |
| `/dashboard/summary` | Resumen de Home. |
| `/analytics/summary` | Indicadores básicos documentados. |
| `/export` | Descargar exportación JSON versionada. |

Los nombres exactos y métodos se pueden ajustar durante implementación sin cambiar el comportamiento requerido. Las operaciones de cambio de estado deben ser explícitas y validadas.

## 10. Estructura de repositorio propuesta

```text
life-os/
├── AGENTS.md
├── README.md
├── VISION.md
├── REQUIREMENTS.md
├── ARCHITECTURE.md
├── DATABASE.md
├── SECURITY.md
├── ROADMAP.md
├── opencode.json
├── .gitignore
├── .opencode/
│   └── skills/
│       ├── lifeos-feature-workflow/SKILL.md
│       ├── lifeos-data-integrity/SKILL.md
│       ├── lifeos-quality-gate/SKILL.md
│       └── lifeos-ui-review/SKILL.md
├── scripts/
│   └── setup-opencode.ps1
├── backend/
│   ├── pyproject.toml
│   ├── alembic.ini
│   ├── migrations/
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/
│   │   ├── core/
│   │   ├── db/
│   │   └── modules/
│   │       ├── tasks/
│   │       ├── projects/
│   │       ├── notes/
│   │       ├── habits/
│   │       ├── dashboard/
│   │       └── analytics/
│   └── tests/
└── frontend/
    ├── index.html
    ├── assets/
    │   ├── css/
    │   └── js/
    └── views/
```

No crear todos los archivos vacíos de antemano. La estructura se incorpora cuando la Fase 1 la necesite. `data/` y `backups/` se crean localmente y quedan fuera de Git.

## 11. Ubicación de datos y ejecución local

- El backend escucha únicamente en `127.0.0.1`, puerto inicial `8000`.
- La UI se sirve desde el mismo origen, evitando CORS.
- Base de datos fuera del repositorio: Windows `%LOCALAPPDATA%\LifeOS\lifeos.db`; Linux `$XDG_DATA_HOME/life-os/lifeos.db` o `~/.local/share/life-os/lifeos.db`; macOS `~/Library/Application Support/LifeOS/lifeos.db`.
- La ruta se puede sustituir mediante `LIFEOS_DATA_DIR`.
- Los backups se guardan en una ubicación de usuario separada y excluida de Git.
- La ejecución y las funciones esenciales no requieren Node.js. Node solo se usa para herramientas auxiliares de OpenCode/skills cuando corresponda.

## 12. Seguridad y privacidad

`SECURITY.md` establece los controles obligatorios. En resumen: bind local, host permitido, sin CORS abierto, entradas validadas en backend, secretos y datos fuera de Git, notas tratadas como texto, logs sin datos privados y pruebas con bases temporales.

No hay autenticación propia en el MVP: el modelo de confianza es la cuenta del sistema operativo del usuario. Esto no protege los archivos frente a otros procesos o personas con acceso a esa cuenta, ni habilita acceso remoto. Cualquier exposición a LAN/Internet requiere un nuevo diseño y aprobación explícita.

## 13. Pruebas y calidad

- Unitarias para servicios y reglas de dominio.
- API para códigos HTTP, validación y respuestas.
- Integración para relaciones, transacciones y eventos.
- Migraciones desde base vacía y una versión de prueba previa.
- Exportación, backup y restauración con datos sintéticos.
- Pruebas de frontend y navegador cuando los flujos principales estén integrados; evitar agregar Playwright al stack antes de justificarlo.
- Nunca utilizar la base de datos personal en tests.

## 14. Dependencias y herramientas

Las versiones exactas de librerías se resolverán al implementar cada fase, usando Context7 y la documentación oficial para APIs que hayan cambiado. Las versiones instaladas deben quedar bloqueadas en el archivo de dependencias.

Python es el runtime de Life OS. Node.js no es requisito de ejecución: el CLI `skills` de desarrollo requiere Node.js 22.20 o superior; se recomienda la LTS vigente en el momento de instalarlo. No agregar bundlers ni paquetes frontend en el MVP.

## 15. Evolución futura

La ruta cloud-ready se basa en separación de servicios y persistencia, no en infraestructura distribuida. Cuando exista una necesidad real, se evaluarán PostgreSQL, autenticación, despliegue HTTPS, backups cifrados, sincronización y proveedores de IA. No diseñar esas piezas antes de conocer sus requisitos.

---

**Regla de implementación:** si una decisión técnica contradice `REQUIREMENTS.md` o `SECURITY.md`, no se aplica sin actualizar primero la documentación y obtener la autorización correspondiente.
