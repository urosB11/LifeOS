# MIND-001 — Diseño funcional y técnico de Mind

**Prioridad:** P1 · **Estado:** PLANNING · **Responsable:** UX/Product + Architecture · **Solo diseño; no implementar.**

## Objetivo
Convertir `docs/product/MIND_PRODUCT_MODEL.md` y `docs/product/ORBES_MODEL.md` en una especificación implementable, sin interrumpir la Fase 9 ni autorizar código.

## Dependencias y restricciones
- Fase 9 mantiene prioridad hasta aceptación del PO.
- No modificar runtime, modelos, migraciones, APIs, dependencias ni configuración.
- No introducir proveedores/modelos reales ni servicios remotos.
- Mantener LifeOS local-first y útil sin IA.
- Revisar arquitectura, base de datos, exportación/backup y seguridad actuales antes de recomendar entidades.

## Entregables
1. **Auditoría de arquitectura existente:** frontend, navegación, módulos Notes/Projects/Tasks, API, persistencia, export/backup y límites relevantes.
2. **Casos de uso y flujos:** Inbox, Spaces, Canvas, captura, edición, conexiones, búsqueda, referencias cruzadas y borrado.
3. **Modelo conceptual y ERD:** contenido canónico, Canvas, nodos, conexiones, grupos, artefactos y referencias. Diferenciar qué requiere persistencia de dominio y qué es estado visual.
4. **Contratos de interacción:** creación, edición, mover, conectar, duplicar referencia, quitar de Canvas, borrar contenido, deshacer/rehacer y recuperación.
5. **UX responsive:** escritorio, tablet y móvil; navegación de Canvas grande; teclado, accesibilidad y alternativas a gestos.
6. **Rendimiento:** tamaño esperado, estrategia de renderizado/virtualización, zoom/pan, guardado y recuperación.
7. **Integridad y portabilidad:** export/import, backup/restore, referencias rotas, versionado, borrado y compatibilidad.
8. **Plan por etapas:** MVP Mind sin IA, integración con entidades LifeOS, Orbes simples, Orbes persistentes/avanzados.
9. **Riesgos y decisiones pendientes:** alternativas, costos, complejidad, pruebas y recomendación.

## Hipótesis de MVP para evaluar
- crear un Space y un Canvas;
- capturar ideas/notas;
- colocar, mover y conectar nodos;
- abrir/editar el contenido canónico desde cualquier representación;
- reutilizar un mismo contenido en varios Canvases sin duplicarlo;
- guardar/restaurar el lienzo;
- Inbox de captura rápida;
- exportación/backup coherente.

Esta lista es una hipótesis para evaluar, no una autorización de implementación.

## Fuera de alcance
- Orbes conectados a modelos reales;
- agentes autónomos o multiagente;
- integraciones externas, sincronización o cloud;
- nuevas dependencias/frameworks sin análisis y aprobación;
- nuevas tablas/migraciones o cambios API;
- automatizaciones que escriban en entidades canónicas.

## Criterios de aceptación del diseño
- cada entidad tiene propósito y fuente de verdad;
- CanvasNode no duplica contenido canónico;
- eliminar una representación no elimina el contenido;
- relaciones semánticas son independientes de posiciones;
- el mismo contenido puede representarse en múltiples canvases;
- el MVP tiene casos de uso y criterios comprobables;
- exportación/backup y recuperación están contemplados;
- decisiones técnicas están justificadas contra la arquitectura real;
- se separa explícitamente lo confirmado, lo propuesto y lo pendiente.

## Entrega
Presentar documento de diseño, ERD, flujos, alternativas y plan por etapas. Dejar REVIEW para decisión del PO. No escribir código.
