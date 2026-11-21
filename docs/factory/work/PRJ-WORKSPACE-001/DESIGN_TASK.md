# PRJ-WORKSPACE-001 — Proyecto como espacio de trabajo

**Prioridad:** P1 · **Estado:** PLANNING · **Responsable:** Product/UX · **Solo diseño; no implementar**

## Contexto

El detalle actual de un proyecto está centrado principalmente en su descripción y lista de tareas. La visión futura de LifeOS es que un proyecto sea un espacio de trabajo para organizar y seguir un resultado, no solo un contenedor de tareas.

El PO quiere explorar, de manera gradual, cómo convivirían tareas, notas, documentos/recursos y seguimiento. Esta tarea no autoriza construir esos módulos todavía.

## Pregunta de diseño

¿Qué información y herramientas necesita tener un proyecto para servir como espacio de trabajo completo, manteniendo una interfaz comprensible y una arquitectura simple?

## Áreas que deben evaluarse

1. **Resumen:** propósito, resultado esperado, estado, fechas importantes y próximo paso.
2. **Planificación:** objetivos, hitos, entregables, criterios de aceptación y fechas planificadas/reales. Coordinar con PRJ-PLAN-001 para no duplicar su modelo de progreso.
3. **Ejecución:** tareas, prioridades, vencimientos y relación con hitos/entregables.
4. **Conocimiento:** notas existentes vinculadas al proyecto, documentos y recursos.
5. **Seguimiento:** actualizaciones periódicas, avances, bloqueos, decisiones, métricas verificables y línea temporal.
6. **Actividad:** cambios relevantes y trazabilidad, sin convertirlo necesariamente en un log exhaustivo.

## Distinciones necesarias

- Nota: contenido editable de texto.
- Documento: determinar si significa archivo local, documento generado o referencia externa.
- Recurso: enlace, referencia o material asociado.
- Entregable: resultado concreto verificable del proyecto; no es sinónimo de documento.
- Hito: punto de control del plan; no es sinónimo de tarea.
- Métrica: valor con fuente, fórmula y período; no inventar valores por falta de datos.

No asumir que se implementarán cargas de archivos. Evaluar compatibilidad con el enfoque local-first, respaldo/exportación, privacidad, tamaño de datos y recuperación.

## Trabajo de diseño

- Definir casos de uso de un proyecto personal, de aprendizaje y de trabajo.
- Proponer arquitectura de información: secciones, navegación, jerarquía y pantalla inicial.
- Comparar pestañas, secciones en una página y vistas de resumen/detalle.
- Definir relaciones entre proyectos, tareas, notas, recursos, documentos, hitos y entregables.
- Identificar qué capacidades ya existen (incluyendo vínculos nota-proyecto) y cuáles serían nuevas.
- Proponer etapas MVP → evolución, evitando implementar todo a la vez.
- Especificar estados vacíos, carga, error, proyecto pequeño y proyecto complejo.
- Evaluar móvil y escritorio.
- Coordinar definiciones de hitos/entregables/progreso con PRJ-PLAN-001 y semántica de métricas con ANALYTICS-001.

## Entregable

Un documento de diseño que incluya:
- principios y objetivos;
- mapa de información y flujos principales;
- wireframe textual o diagrama de secciones;
- entidades y relaciones conceptuales;
- decisiones pendientes y alternativas;
- capacidades reutilizadas vs nuevas;
- fases recomendadas, dependencias y riesgos;
- criterios de aceptación para una futura especificación de implementación.

## Límites

- No modificar código, modelos, migraciones, API ni base de datos.
- No crear adjuntos ni almacenamiento de archivos.
- No agregar dependencias ni servicios.
- No cambiar la visión del producto ni aprobar alcance por iniciativa propia.
- No convertir todas las ideas en requisitos inmediatos.

La implementación necesitará una tarea READY independiente y aprobación explícita del PO.