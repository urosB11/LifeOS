# Life OS — Política y diseño de seguridad

**Estado:** línea base de seguridad para el MVP local 0.1
**Versión:** 0.2
**Fecha:** 17 de noviembre de 2026
**Relacionado con:** `VISION.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md`, `DATABASE.md` y `AGENTS.md`

> Life OS se diseña inicialmente para un usuario, ejecutándose en su computadora. Escuchar en localhost reduce la exposición, pero no reemplaza la seguridad del sistema operativo ni convierte a la aplicación en un servicio listo para Internet.

## 1. Objetivo y modelo de confianza

La primera versión tendrá:

- backend local ligado exclusivamente a `127.0.0.1:8000`;
- UI servida por FastAPI en el mismo origen;
- SQLite fuera del repositorio;
- sin login propio, usuarios múltiples ni roles;
- sin telemetría ni transmisión de datos personales;
- sin integraciones externas ni proveedor de IA;
- operación básica disponible sin Internet.

El modelo confía en la cuenta y sesión del sistema operativo. No protege los datos frente a malware, acceso físico a una sesión desbloqueada, otro proceso con los mismos permisos o personas que puedan leer los archivos de datos/backups.

## 2. Principios

1. Mínima exposición de red.
2. Privacidad local y minimización de datos.
3. Validación y autorización en backend, no solo frontend.
4. Propiedad, exportación y recuperación de datos.
5. Dependencias y permisos mínimos.
6. No ejecutar código arbitrario descargado ni delegar decisiones sensibles sin control.

## 3. Red y exposición

- El servidor escucha en `127.0.0.1`, puerto inicial `8000`.
- No cambiar a `0.0.0.0`, abrir firewall ni habilitar acceso LAN/Internet en el MVP.
- Servir frontend y API desde el mismo origen; mantener CORS deshabilitado salvo que se justifique y revise una necesidad futura.
- Validar el encabezado `Host` con una lista local permitida (`127.0.0.1:8000` y `localhost:8000`, según el modo de acceso configurado).
- Rechazar hosts desconocidos para reducir riesgo de DNS rebinding.
- No confiar en `Origin`, `Referer` o `Host` como sustituto de autenticación para un futuro despliegue remoto.
- Mantener el API en loopback incluso durante pruebas manuales.

## 4. Autenticación y control de acceso

El MVP no implementa un login propio porque se ejecuta localmente para un usuario. Esto es una decisión de alcance, no una garantía de seguridad. Los archivos quedan protegidos por los permisos de la cuenta del sistema operativo.

Antes de cualquier acceso remoto, multiusuario o exposición a LAN será obligatorio diseñar e implementar autenticación, autorización por operación, HTTPS, gestión de sesiones, protección CSRF, límites de tasa, registro de seguridad y recuperación de cuentas. No reutilizar el supuesto de confianza local fuera del equipo.

## 5. Protección de datos locales

### 5.1 Ubicación y permisos

- Base de datos y backups fuera del repositorio, en las rutas definidas en `DATABASE.md`.
- Crear directorios de datos con permisos restrictivos compatibles con el sistema operativo.
- No usar carpetas sincronizadas públicamente ni directorios temporales para la base activa.
- No guardar información privada en logs, nombres de archivos ni mensajes de error.

### 5.2 Secretos y configuración

- No hay secretos de aplicación en el MVP.
- Futuras claves API se guardarán fuera del código y Git, mediante variables de entorno o almacén seguro del sistema.
- No guardar secretos en `user_preferences`, JSON exportado o actividad.
- `.env` queda excluido; solo puede versionarse `.env.example` con nombres y valores ficticios.

### 5.3 Backup y exportación

- Exportaciones JSON y backups contienen datos personales y deben tratarse como la base original.
- No almacenarlos en Git, repositorios públicos ni servicios externos automáticamente.
- Utilizar la API backup de SQLite para garantizar consistencia.
- Probar restauración en base temporal; crear backup previo antes de reemplazar la base activa.
- El cifrado de backups no es requisito del MVP, pero es una condición a evaluar antes de incorporar información financiera, credenciales o datos de alta sensibilidad.

## 6. Validación de entradas y aplicación

- Validar todo dato recibido en backend con esquemas explícitos.
- Limitar longitud de títulos, descripciones, nombres de etiquetas y contenido de notas; los límites concretos se centralizan y documentan en el código.
- Normalizar nombres de etiquetas y validar estados/prioridades contra conjuntos permitidos.
- Utilizar parámetros SQL/ORM; nunca concatenar texto del usuario en SQL.
- Renderizar contenido de notas como texto mediante APIs seguras del DOM (`textContent`); no usar `innerHTML` con contenido del usuario.
- No ejecutar HTML, scripts, expresiones, archivos ni contenido activo ingresado por el usuario.
- Validar archivos y formatos si se incorporan en etapas futuras.
- Operaciones destructivas requieren confirmación en la interfaz y validación de reglas en backend.
- Mantener transacciones atómicas para cambios de dominio y sus eventos.

## 7. Logs y actividad

- Los logs técnicos no deben guardar cuerpos de notas, descripciones privadas, tokens, rutas con información sensible ni bases de datos.
- `activity_events` almacena eventos mínimos y metadatos con lista permitida; no es un log de contenido.
- No incluir datos de usuarios en stack traces presentados en la interfaz.
- Los errores se registran de forma útil para depuración sin exponer rutas o información sensible al navegador.
- La retención y rotación de logs técnicos se definirá antes de habilitar sesiones largas o un servicio persistente.

## 8. Dependencias, plugins y skills

- Añadir una dependencia solo si resuelve una necesidad del MVP y tiene mantenimiento/documentación razonables.
- Revisar procedencia, licencia, cambios, scripts de instalación y avisos de auditoría de skills/plugins antes de incorporarlos.
- No ejecutar scripts incluidos en una skill sin inspeccionarlos y comprender sus efectos.
- Las skills son instrucciones para el agente, no una frontera de seguridad ni un permiso para ejecutar acciones.
- Context7 se utiliza durante el desarrollo para documentación pública de paquetes. No enviar notas, base de datos, credenciales, archivos `.env`, contenido privado ni fragmentos sensibles a la consulta.
- El plugin Context7 no debe convertirse en dependencia de ejecución de Life OS; la aplicación funciona si Context7 está desconectado.
- Las skills y herramientas instaladas no pueden cambiar las restricciones de este documento.

## 9. Pruebas de seguridad

Como mínimo:

- verificar el bind local y rechazo de host no permitido;
- comprobar ausencia de CORS abierto;
- validar entradas inválidas y límites de longitud;
- comprobar que las notas se muestran como texto y no ejecutan HTML/JS;
- comprobar las reglas de borrado y relaciones;
- revisar logs y eventos para descartar contenido privado;
- revisar `git status` y el diff para detectar secretos, bases o backups;
- probar backup/restauración con información sintética.

## 10. Respuesta a incidentes

Ante pérdida, corrupción o sospecha de acceso no autorizado:

1. detener la aplicación si sigue realizando escrituras;
2. no sobrescribir ni borrar archivos originales;
3. conservar una copia de la base y los logs técnicos relevantes;
4. identificar el último backup verificable;
5. restaurar primero en un entorno de prueba;
6. confirmar la integridad de los datos antes de reemplazar la base activa;
7. documentar causa y medidas para evitar recurrencia.

## 11. Condiciones para acceso remoto futuro

No habilitar acceso remoto hasta contar con:

- modelo de amenazas actualizado;
- autenticación y autorización;
- HTTPS y despliegue seguro;
- gestión y rotación de secretos;
- protección CSRF, CORS exacto y validación de origen;
- límites de tasa, logs y alertas apropiadas;
- backups cifrados y restauración probada;
- revisión de dependencias y pruebas de seguridad;
- aprobación explícita del usuario.

## 12. Decisiones y límites actuales

No hay login, cifrado propio, exposición a LAN/Internet, telemetría, proveedores de IA ni integraciones externas en el MVP. No se protege frente a un sistema operativo comprometido o frente a otras personas con acceso a la misma cuenta. Estos límites deben comunicarse claramente y no ocultarse con la etiqueta “local seguro”.

---

**Regla para agentes:** ante cualquier conflicto, `SECURITY.md` prevalece sobre la conveniencia de una implementación. Una excepción requiere explicar riesgos y alternativas y obtener autorización explícita antes de cambiar el comportamiento.
