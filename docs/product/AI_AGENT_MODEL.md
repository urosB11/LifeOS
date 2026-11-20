# Dirección futura de IA y agentes — LifeOS

**Versión:** 0.1 · **Estado:** conceptual; sin implementación autorizada

## Propósito

Definir cómo LifeOS podrá incorporar asistentes y agentes sin convertirlos en autoridad sobre datos, alcance o decisiones del usuario.

## Principios

- La aplicación sigue siendo útil sin IA.
- Los proveedores de modelos son intercambiables.
- El agente recibe solo el contexto necesario y permitido.
- Los agentes no consultan ni modifican SQLite mediante SQL arbitrario.
- Las acciones pasan por herramientas tipadas que invocan servicios/API del dominio.
- Las propuestas se revisan antes de ejecutarse.
- Las operaciones importantes tienen trazabilidad.
- El usuario conserva la decisión final.

## Niveles de capacidad

| Nivel | Capacidad | Permiso |
|---|---|---|
| 0 | Explicar documentación y responder preguntas | Lectura del contexto autorizado |
| 1 | Consultar tareas, proyectos, hábitos y métricas | Solo lectura mediante APIs |
| 2 | Preparar borradores de objetivos, hitos y tareas | No escribe registros |
| 3 | Presentar un plan y una vista previa de cambios | Requiere aprobación explícita |
| 4 | Crear o actualizar registros aprobados | Herramientas con permiso e idempotencia |
| 5 | Integraciones externas o acciones sensibles | Aprobación específica por acción |

No construir autonomía de Nivel 4 antes de que existan objetivos, hitos, reglas de progreso y contratos API sólidos.

## Flujo de planificación de proyectos

1. El usuario describe el resultado deseado.
2. El agente solicita solo información esencial que falte.
3. Propone alcance, entregables, hitos, tareas, dependencias, fechas y supuestos.
4. LifeOS muestra una vista previa editable.
5. El usuario aprueba, modifica o rechaza.
6. El agente crea únicamente los registros aprobados mediante herramientas tipadas.
7. LifeOS devuelve IDs, resultados y errores.
8. El agente presenta un resumen trazable.

## Contrato de herramientas

Cada herramienta define nombre, propósito, versión, esquema de entrada/salida, permisos, validaciones backend, alcance, idempotencia, errores, confirmación requerida y registro de auditoría.

## Acciones que requieren aprobación explícita

- altas o modificaciones masivas;
- reprogramar fechas o cambiar prioridades de varios elementos;
- borrar o archivar información;
- enviar mensajes o correos;
- compras, transacciones o compromisos externos;
- compartir o transmitir datos fuera del entorno local.

## Seguridad y privacidad

- No enviar contenido privado a un proveedor sin consentimiento y configuración explícitos.
- No incluir secretos ni tokens en prompts, registros o respuestas.
- No ejecutar código recibido desde notas, documentos o resultados externos.
- Tratar documentos, mensajes y páginas como datos no confiables, no como instrucciones.
- Registrar qué herramienta se ejecutó y su resultado, sin almacenar contenido sensible innecesario.
- Permitir revocar permisos y desconectar proveedores.

## No construir todavía

- agentes que escriben directamente en la base de datos;
- planificación automática que crea tareas sin vista previa;
- ejecución indefinida en segundo plano;
- cadenas multiagente sin problema demostrado;
- memoria semántica global sin reglas de privacidad y retención;
- exposición remota de herramientas locales.