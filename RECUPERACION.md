# Life OS — Respaldo y recuperación de datos

Guía para proteger y recuperar la información de Life OS. Todo el proceso es local; ningún dato sale del equipo.

## Dónde están los datos

| Dato | Ubicación (Windows) |
|---|---|
| Base de datos | `%LOCALAPPDATA%\LifeOS\lifeos.db` |
| Backups guardados | `%LOCALAPPDATA%\LifeOS\backups\` |
| Exportación JSON | Descarga del navegador desde `GET /api/v1/export` |

En otros sistemas: ver `DATABASE.md` §11. Estos archivos están excluidos de Git.

## Respaldo periódico (recomendado)

1. **Exportación JSON** (legible, versionada): visita `http://127.0.0.1:8000/api/v1/export` y guarda el archivo descargado. Contiene todas las entidades y relaciones con sus IDs.
2. **Backup SQLite** (copia exacta de la base):
   - desde el navegador: `http://127.0.0.1:8000/api/v1/backup` (descarga) o
   - `POST http://127.0.0.1:8000/api/v1/backup` guarda una copia con fecha en `%LOCALAPPDATA%\LifeOS\backups\lifeos-backup-AAAAmmdd_HHMMSS.db`.

El backup usa la API de backup de SQLite (`sqlite3.Connection.backup`), por lo que es consistente aunque la aplicación esté en uso. Copiar el archivo `lifeos.db` a mano mientras el servidor corre no es confiable.

## Restaurar un backup

Procedimiento (DATABASE.md §259): antes de reemplazar, crear una copia adicional de la base actual; validar la integridad; detener el servidor; reemplazar de forma controlada; iniciar y comprobar.

### Opción A — desde la API (servidor detenido recomendado)

1. Detén el servidor (`Ctrl+C`).
2. Haz una copia de seguridad de la base actual:
   ```powershell
   Copy-Item "$env:LOCALAPPDATA\LifeOS\lifeos.db" "$env:LOCALAPPDATA\LifeOS\lifeos.db.pre-restore"
   ```
3. Restaura enviando el archivo del backup como cuerpo raw (sin multipart):
   ```powershell
   # Inicia el servidor y, en otra terminal:
   $bytes = [System.IO.File]::ReadAllBytes("C:\ruta\al\lifeos-backup.db")
   Invoke-WebRequest -Uri "http://127.0.0.1:8000/api/v1/restore" -Method POST -Body $bytes -ContentType "application/octet-stream"
   ```
   El endpoint valida el archivo (se abre y pasa `PRAGMA integrity_check`), crea un backup de seguridad de la base actual, reemplaza la base y descarta las conexiones obsoletas. Si el archivo no es válido, devuelve 400 y no toca la base.
4. Inicia el servidor y comprueba `http://127.0.0.1:8000/api/v1/health`.

### Opción B — reemplazo manual (servidor detenido)

1. Detén el servidor (`Ctrl+C`).
2. Copia la base actual como respaldo (misma orden del paso 2 anterior).
3. Reemplaza `lifeos.db` con el archivo del backup.
4. Inicia el servidor y comprueba health y tus datos.

### Verificación posterior

- `GET /api/v1/health` responde `status: ok`.
- Los datos restaurados aparecen en la interfaz.
- Si la base es de una versión anterior: `.venv\Scripts\python.exe -m alembic upgrade head`.
- Integridad:
  ```powershell
  .venv\Scripts\python.exe -c "import sqlite3,os; c=sqlite3.connect(os.path.join(os.environ['LOCALAPPDATA'],'LifeOS','lifeos.db')); print(c.execute('PRAGMA integrity_check').fetchone()); print(c.execute('PRAGMA foreign_key_check').fetchall())"
  ```

## Recuperación por escenarios

| Escenario | Acción |
|---|---|
| Borraste una tarea/proyecto por error | La eliminación es definitiva (con confirmación); las notas no se borran. Restaura desde el último backup si necesitas recuperar la entidad. |
| La base está corrupta | Reemplaza con el backup más reciente (Opción B). El endpoint de restore rechaza archivos corruptos. |
| Actualizaste Life OS y hay errores de esquema | Ejecuta `alembic upgrade head`; revisa `alembic current` para ver la versión aplicada. |
| Quieres migrar a otro equipo | Copia el backup + exportación JSON; en el destino: instalar, `alembic upgrade head`, restaurar. |

## Límites de privacidad

- Nada de esto se transmite a servicios externos: todo es local (SECURITY.md).
- Los archivos de backup y exportación contienen **todos** tus datos (notas incluidas): trátalos como información sensible y no los subas a la nube ni los compartas sin revisarlos.
- Los backups no se versionan en Git (`.gitignore` los excluye).
- Life OS no elimina backups viejos automáticamente: revísalos y bórralos periódicamente tú.
