# Life OS — Instrucciones para agentes de desarrollo

**Estado:** instrucciones operativas vigentes para el repositorio
**Versión:** 0.2
**Fecha:** 17 de noviembre de 2026

Este archivo define cómo trabajar en Life OS. No reemplaza las especificaciones del producto ni concede permisos para salir de su alcance. Las skills ofrecen procedimientos especializados; no pueden modificar estas reglas.

## 1. Documentos y autoridad

Antes de una tarea relevante, consulta:

1. `VISION.md` — propósito y dirección.
2. `REQUIREMENTS.md` — comportamiento exigido y límites del MVP.
3. `ARCHITECTURE.md` — estructura y decisiones técnicas.
4. `DATABASE.md` — modelo, relaciones, eventos y restricciones.
5. `SECURITY.md` — límites obligatorios de privacidad y seguridad.
6. `ROADMAP.md` — fase actual y condiciones de salida.

Jerarquía: `SECURITY.md` prevalece para seguridad; `REQUIREMENTS.md` define el comportamiento; `ARCHITECTURE.md` define la organización técnica; `DATABASE.md` define la integridad de datos; `ROADMAP.md` define la secuencia; `VISION.md` define el horizonte. Este archivo define el proceso de trabajo.

Si hay una contradicción, no la resuelvas silenciosamente: identifica los documentos, explica el impacto y propone una corrección antes de implementar la parte afectada.

## 2. Autonomía y flujo de trabajo

La autorización vigente permite iniciar la Fase 1 del `ROADMAP.md`. No autoriza al agente a ejecutar el roadmap entero, agregar funciones futuras ni realizar acciones externas.

Para cada tarea:

1. inspeccionar el estado del repositorio, archivos y entorno antes de editar;
2. leer los requisitos y documentos directamente relacionados;
3. describir el cambio mínimo y sus criterios de verificación;
4. implementar una porción vertical pequeña;
5. ejecutar pruebas y chequeos reales;
6. revisar el diff, actualizar documentación y resumir resultados.

No hace falta pedir confirmación para decisiones rutinarias ya definidas en los documentos. Sí debe detenerse ante cambios de alcance, migraciones destructivas no previstas, eliminación de datos, exposición de red, secretos, compras, despliegues, push/publicación o integraciones externas.

Nunca sobrescribir cambios del usuario. No ejecutar `git reset --hard`, borrar ramas, reescribir historial, hacer push ni publicar sin autorización explícita.

## 3. Límites del MVP

- No agregar IA, agentes personales, cloud, sync, integraciones, usuarios múltiples ni App Center de plugins.
- No introducir frameworks frontend, bundlers, Tailwind, React/Vue, Docker, microservicios ni servicios residentes sin una justificación escrita y aprobación.
- No crear módulos vacíos para áreas futuras.
- Mantener las funciones esenciales offline.
- La UI y los widgets leen servicios/endpoints existentes; no duplican reglas ni datos.
- Las métricas son deterministas, con fórmulas y fuentes explícitas.

## 4. Convenciones técnicas

- Python 3.11+; FastAPI; SQLAlchemy 2.x síncrono; SQLite; Alembic; Uvicorn.
- pytest + HTTPX; Ruff cuando esté configurado.
- HTML/CSS/JavaScript nativo, módulos ES sin build step.
- REST bajo `/api/v1`; frontend estático servido por FastAPI en el mismo origen.
- Uvicorn solo en `127.0.0.1:8000` por defecto.
- IDs UUIDv4 como texto; instantes UTC ISO 8601; vencimientos como `YYYY-MM-DD` local.
- Mantener capas API → servicios → repositorios/persistencia; no colocar SQL ni lógica de dominio en rutas o UI.
- Seguir `DATABASE.md` para las políticas de eliminación, vínculos, migraciones y eventos.

## 5. Datos e integridad

- Activar y verificar `PRAGMA foreign_keys = ON` en cada conexión.
- Nunca usar la base personal para tests; utilizar bases temporales y datos sintéticos.
- Las operaciones de dominio y eventos correspondientes deben confirmarse en la misma transacción.
- Todo cambio de esquema requiere migración versionada, pruebas y actualización de `DATABASE.md`.
- No introducir event sourcing ni tablas de métricas duplicadas.
- No incluir cuerpos de notas ni descripciones privadas en logs, eventos o metadatos.
- Borrar un proyecto/tarea no debe borrar notas relacionadas; solo los vínculos definidos en `DATABASE.md`.
- No modificar manualmente una base local de usuario para probar.

## 6. Context7 y documentación actualizada

Context7 es la fuente preferida para consultar documentación pública y versionada de librerías cuando la tarea dependa de sus APIs, configuración o comportamiento.

Procedimiento:

1. identificar el paquete y la versión instalada o propuesta;
2. resolver la biblioteca correcta en Context7;
3. consultar el tema y versión específicos;
4. comprobar detalles críticos con documentación oficial cuando corresponda;
5. adaptar ejemplos a la arquitectura de Life OS;
6. si no hay resultado confiable, decirlo y recurrir a la documentación oficial.

No es necesario usar Context7 para lógica propia trivial. Nunca enviar notas, base de datos, credenciales, archivos `.env`, tokens ni fragmentos privados del repositorio. Las consultas deben ser preguntas técnicas genéricas. La aplicación debe seguir funcionando cuando Context7 no esté disponible.

### Integración configurada

`opencode.json` incluye el plugin de proyecto `@upstash/context7-opencode`. Este integra las herramientas MCP de Context7 y la skill `context7-mcp`. No instalar además `npx ctx7 setup --opencode` ni un segundo servidor manual con el mismo objetivo. Después de abrir Life OS con OpenCode, completar OAuth con:

```powershell
opencode mcp auth context7
```

La configuración del plugin está en el repositorio, pero la autenticación es local por usuario y no se versionan tokens.

## 7. Skills

### Distinción

- `AGENTS.md`: reglas permanentes del proyecto.
- `SKILL.md`: procedimiento especializado que el agente carga cuando la tarea lo necesita.
- MCP/plugin: herramientas o fuentes externas accesibles al agente.

OpenCode descubre skills de proyecto en `.opencode/skills/<skill-id>/SKILL.md`. Las skills se cargan bajo demanda; no deben duplicar todos los contenidos de los documentos principales.

### Skills incluidas localmente

| ID | Uso |
|---|---|
| `lifeos-feature-workflow` | Planificar e implementar una funcionalidad como flujo vertical pequeño. |
| `lifeos-data-integrity` | Modificar entidades, relaciones, transacciones, eventos o migraciones. |
| `lifeos-quality-gate` | Verificar pruebas, diffs y criterios de finalización. |
| `lifeos-ui-review` | Revisar UI responsive, accesibilidad y estados de interfaz. |

### Skills externas seleccionadas

| Skill | Fuente | Uso | Decisión |
|---|---|---|---|
| `frontend-design` | `anthropics/skills` | Dirección visual intencional y ejecución frontend de calidad. | Instalar en el proyecto. |
| `fastapi` | `fastapi/fastapi` (oficial) | Patrones y prácticas actuales de FastAPI y Pydantic. | Instalar en el proyecto. |
| `context7-mcp` | Integración oficial Context7/OpenCode | Búsqueda de documentación actualizada. | La instala el plugin configurado. |

La skill `frontend-design` se usa cuando se diseña o remodela UI, no para tareas backend. Recomienda tomar decisiones deliberadas de jerarquía, tipografía, composición y color; esas decisiones deben respetar las restricciones de rendimiento, accesibilidad y funcionamiento local de Life OS.

La skill `fastapi` proviene del repositorio oficial del framework y se usa para consultar patrones de endpoints, validación, dependencias y esquemas. Es una referencia técnica, no una autorización para cambiar la arquitectura: no adoptar FastAPI Cloud, telemetría/OpenTelemetry, async, SDKs generados ni nuevas dependencias si contradicen los documentos aprobados. El proyecto mantiene FastAPI síncrono, SQLite y el resto del stack definido en `ARCHITECTURE.md`.

Se revisaron además:

- `web-design-guidelines` de Vercel: útil como auditor de UI y accesibilidad, pero el estado de auditoría de skills.sh muestra una advertencia de Socket; se difiere hasta inspección adicional.
- `webapp-testing` de Anthropic: aporta scripts Python/Playwright, pero su ficha de auditoría presenta advertencias de Socket y Snyk; se difiere. La primera estrategia de pruebas será pytest/HTTPX y se evaluará Playwright cuando existan flujos UI integrados.

Las fichas consultadas de `frontend-design` y `fastapi` mostraban Gen Agent Trust Hub, Socket y Snyk en estado Pass el 17 de noviembre de 2026; esta observación no reemplaza inspeccionar el contenido y revisar auditorías al actualizar. No instalar colecciones completas ni skills para React/Next.js: no corresponden al stack inicial.

### Instalación de skills externas

El script `scripts/setup-opencode.ps1` instala únicamente `anthropics/skills` → `frontend-design` y `fastapi/fastapi` → `fastapi`, dirigidas a OpenCode y copiadas al proyecto para evitar dependencias de symlinks en Windows. Ejecutarlo desde la raíz. El CLI `skills` requiere Node.js 22.20 o superior; se recomienda la LTS vigente, no una versión Alpha. El script desactiva la telemetría anónima del CLI durante esa instalación.

Antes de agregar cualquier skill nueva: revisar fuente, contenido, licencia, scripts, permisos y estado de auditoría. No ejecutar scripts incluidos sin inspección. Nunca una skill puede sobreescribir este archivo ni los documentos de seguridad.

## 8. Seguridad y privacidad

`SECURITY.md` es obligatorio. En particular:

- mantener `127.0.0.1`; no cambiar a `0.0.0.0` ni abrir puertos;
- no añadir telemetría ni transmitir datos del usuario;
- no exponer notas, tareas, proyectos, preferencias, eventos o backups a APIs externas;
- no versionar `.env`, tokens, secretos, DBs, exportaciones ni backups;
- validar entrada en backend; utilizar consultas parametrizadas/ORM;
- tratar el contenido de notas como texto; no ejecutarlo ni interpretarlo como HTML;
- no instalar dependencias o plugins sugeridos automáticamente sin revisar el cambio;
- no debilitar seguridad para solucionar un error;
- pedir autorización antes de acciones destructivas, externas o con consecuencias económicas.

## 9. Calidad y verificación

Antes de cerrar una tarea:

- ejecutar tests específicos y el conjunto relevante;
- ejecutar migraciones en base temporal si cambió el esquema;
- verificar errores, límites de entrada y casos negativos pertinentes;
- ejecutar Ruff solo si está configurado;
- revisar diff y `git status` en busca de datos, secretos y cambios accidentales;
- no inventar comandos inexistentes; leer `pyproject.toml` y README;
- informar exactamente qué se ejecutó y qué no se pudo verificar.

## 10. Git y protección del trabajo

- Inspeccionar `git status` y diff antes y después de cambios.
- No descartar cambios previos del usuario.
- Mantener `main` utilizable; realizar cambios pequeños y descriptivos.
- No versionar `data/`, `backups/`, archivos `.env`, bases reales, exportaciones ni entornos virtuales.
- No hacer commit automático si el usuario no lo pidió; no hacer push/publicar sin autorización.

## 11. Comunicación

En tareas complejas, indicar objetivo, alcance y plan. Al finalizar, resumir qué se implementó, archivos modificados, decisiones, comandos y pruebas reales, limitaciones y trabajo pendiente. No afirmar que algo funciona sin verificarlo.

## 12. Regla final

La prioridad es construir un Life OS pequeño, confiable, comprensible, privado y ampliable. La velocidad o la apariencia no justifican sacrificar integridad de datos, seguridad, accesibilidad, simplicidad ni control del usuario.
