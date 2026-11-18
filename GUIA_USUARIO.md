# Life OS — Guía de usuario

Guía breve para usar Life OS (Life OS 0.2) en tu equipo. Todo funciona localmente y sin conexión a Internet.

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

La cabecera tiene seis secciones: **Home**, **Proyectos**, **Tareas**, **Notas**, **Hábitos** y **Configuración**.

### Home (dashboard)

- **Resumen:** tareas pendientes, completadas, vencidas y proyectos activos.
- **Widgets:** próximas tareas, proyectos activos, agregar tarea, agregar nota rápida, hábitos de hoy y semana de hábitos.
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

### Hábitos

- **Crear:** nombre obligatorio; descripción, categoría, color, fecha de inicio y frecuencia opcionales. La frecuencia es *Todos los días* o *Días específicos* (elige lunes a domingo).
- **Modalidad:** binario (marcar hecho) o con cantidad objetivo (por ejemplo 5 km); si registras una cantidad igual o mayor a la meta, el día cuenta como cumplido.
- **Hoy:** muestra los hábitos programados para hoy. Puedes *Marcar hecho*, *Omitir*, *Guardar* una cantidad o *Deshacer* un registro.
- **Métricas:** racha actual, mejor racha, cumplimiento de la semana y del mes, y consistencia. Solo cuentan los días programados; si no hay datos suficientes se muestra "Sin datos" en lugar de 0 %.
- **Calendario:** por hábito, con el estado de cada día del mes (cumplido, registrado sin completar, omitido, pendiente y no programado).
- **Acciones:**
  - *Pausar* / *Reactivar*: detiene temporalmente el seguimiento sin borrar nada.
  - *Archivar* / *Restaurar*: guarda el hábito con su historial; es la operación preferida frente a eliminar.
  - *Eliminar*: solo funciona si el hábito no tiene registros; si los tiene, archívalo.
- **Reglas:** no se pueden registrar días futuros ni días que no estén programados; cada día tiene un único registro que puedes corregir o borrar.

### Configuración

- **Tema:** Sistema (sigue el tema del sistema operativo), Claro u Oscuro.
- **Zona horaria:** zona IANA (por ejemplo `America/Argentina/Cordoba`); se usa para fechas y tareas vencidas.
- **Widgets del dashboard:** visibilidad y orden, iguales a los del botón "Editar widgets" de Home.

## Exportar y respaldar

- **Exportación JSON:** `GET /api/v1/export` descarga todas las entidades y relaciones en un archivo versionado.
- **Backup SQLite:** `GET /api/v1/backup` descarga una copia consistente de la base; `POST /api/v1/backup` la guarda en el directorio de backups.

El procedimiento completo de restauración y recuperación está en `RECUPERACION.md`.

## Límites (versión 0.2)

- Un solo usuario, local, sin nube ni sincronización.
- Sin IA, notificaciones ni integraciones externas.
- Las notas son texto plano (sin adjuntos ni formato enriquecido).
- Las métricas son básicas (resumen e indicadores con fórmulas documentadas en `ARCHITECTURE.md` y `DATABASE.md`).
- Los hábitos no tienen recordatorios ni gamificación: el seguimiento es manual.

## Problemas frecuentes

| Síntoma | Solución |
|---|---|
| "Servicio no disponible" | Verifica que Uvicorn esté corriendo en `127.0.0.1:8000`. |
| Página en blanco o sin estilos | Recarga con `Ctrl+F5`; el frontend se sirve desde el mismo origen. |
| "Host no permitido" (400) | Accede solo por `http://127.0.0.1:8000/` o `http://localhost:8000/`. |
| Error tras actualizar la versión | Ejecuta `alembic upgrade head` (ver `RECUPERACION.md`). |
