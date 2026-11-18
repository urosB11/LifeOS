# Life OS — Guía de usuario

Guía breve para usar Life OS (MVP 0.1) en tu equipo. Todo funciona localmente y sin conexión a Internet.

## Iniciar y detener

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000/` en el navegador. Para detener, cierra la terminal con `Ctrl+C`.

- La aplicación solo escucha en tu equipo (`127.0.0.1`); nadie desde la red puede acceder.
- El indicador "Servicio activo" en la cabecera confirma que la conexión con los datos funciona.
- Si dice "Servicio no disponible", revisa que el servidor esté corriendo.

## Navegación

La cabecera tiene cinco secciones: **Home**, **Proyectos**, **Tareas**, **Notas** y **Configuración**.

### Home (dashboard)

- **Resumen:** tareas pendientes, completadas, vencidas y proyectos activos.
- **Widgets:** próximas tareas, proyectos activos, agregar tarea y agregar nota rápida.
- **Editar widgets:** el botón al final permite mostrar/ocultar widgets y reordenarlos con las flechas. "Guardar preferencias" conserva el orden al reiniciar.

### Tareas

- **Crear:** título (obligatorio), proyecto, prioridad (baja/normal/alta) y vencimiento (`YYYY-MM-DD`).
- **Filtrar:** por estado (pendientes/completadas) o por proyecto.
- **Acciones por fila:**
  - *Completar* / *Reabrir*: cambia el estado.
  - *Elimina*: pide confirmación. Al eliminar una tarea, sus notas no se borran; solo se quita el vínculo.

### Proyectos

- **Crear:** nombre obligatorio y descripción opcional.
- **Acciones por estado:**
  - `active`: *Completar* o *Archivar*.
  - `completed`: *Reabrir* o *Archivar*.
  - `archived`: *Restaurar* (vuelve a activo).
- **Eliminar:** solo se permite si el proyecto no tiene tareas. Archivar es la operación preferida: no elimina nada.

### Notas

- **Crear:** título obligatorio, contenido de texto y etiqueta opcional.
- **Buscar:** por coincidencia parcial en título o contenido.
- **Filtrar por etiqueta** y crear etiquetas reutilizables (sin duplicados aunque cambien mayúsculas o espacios).
- **Ver:** muestra la nota completa con sus etiquetas. El contenido se muestra como texto; nunca se ejecuta HTML ni JavaScript.
- **Relaciones:** desde la API una nota puede vincularse a varios proyectos y tareas (`/api/v1/notes/{id}/projects` y `/tasks`), y las notas de un proyecto o tarea se consultan con `GET /api/v1/notes?project_id=...` o `?task_id=...`.

### Configuración

- **Tema:** Sistema (sigue el tema del sistema operativo), Claro u Oscuro.
- **Zona horaria:** zona IANA (por ejemplo `America/Argentina/Cordoba`); se usa para fechas y tareas vencidas.
- **Widgets del dashboard:** visibilidad y orden, iguales a los del botón "Editar widgets" de Home.

## Exportar y respaldar

- **Exportación JSON:** `GET /api/v1/export` descarga todas las entidades y relaciones en un archivo versionado.
- **Backup SQLite:** `GET /api/v1/backup` descarga una copia consistente de la base; `POST /api/v1/backup` la guarda en el directorio de backups.

El procedimiento completo de restauración y recuperación está en `RECUPERACION.md`.

## Límites del MVP 0.1

- Un solo usuario, local, sin nube ni sincronización.
- Sin IA, notificaciones ni integraciones externas.
- Las notas son texto plano (sin adjuntos ni formato enriquecido).
- Las métricas son básicas (resumen e indicadores con fórmulas documentadas en `ARCHITECTURE.md`).

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| "Servicio no disponible" | Verifica que Uvicorn esté corriendo en `127.0.0.1:8000`. |
| Página en blanco o sin estilos | Recarga con `Ctrl+F5`; el frontend se sirve desde el mismo origen. |
| "Host no permitido" (400) | Accede solo por `http://127.0.0.1:8000/` o `http://localhost:8000/`. |
| Error tras actualizar la versión | Ejecuta `alembic upgrade head` (ver `RECUPERACION.md`). |
