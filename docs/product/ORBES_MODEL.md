# Orbes — Modelo funcional futuro

**Versión:** 0.2  
**Estado:** visión aprobada; fuera del MVP y de las primeras entregas de Mind.  
**Fecha:** 22 de noviembre de 2026

## 1. Propósito y prioridad

Los Orbes son asistentes contextuales opcionales dentro de Mind. No son el núcleo de la aplicación y no deben condicionar su arquitectura funcional básica.

Mind debe estar completo y ser útil sin Orbes. Su desarrollo solo comienza cuando Canvas, Cards, documentos, búsqueda, persistencia e integración con LifeOS tengan una base estable.

## 2. Interacción principal: Orbe por tarjeta

La experiencia principal imaginada es una pequeña acción Orbe en una tarjeta. Al activarla, se abre un mini-chat compacto asociado a esa tarjeta, sin sacar al usuario de su trabajo ni ocupar toda la pantalla.

El mini-chat:
- conoce el contexto autorizado de la tarjeta;
- permite hacer preguntas sobre ese contenido;
- puede resumir, explicar, comparar, extraer puntos clave o elaborar un informe;
- puede preparar una propuesta vinculada a esa tarjeta;
- puede expandirse si la tarea requiere una conversación más extensa.

El mismo patrón puede extenderse a una selección de tarjetas, un grupo, un Canvas o un Space. La presencia visual del Orbe debe ser discreta y contextual; no todos los objetos necesitan mostrar un control permanente si eso agrega ruido.

## 3. Comandos y tareas futuras

Ejemplos de interacción:
- “Resumí esta tarjeta”.
- “Prepará un informe sobre este tema”.
- “Convertí estos pasos en tareas”.
- “Creá una tarea para revisar este punto”.
- “Explicame este concepto con un ejemplo”.
- “Compará estas dos fuentes”.
- “Proponé conexiones entre estos conceptos”.

Los ejemplos describen capacidades futuras, no autorizan su implementación inmediata.

## 4. Voz

La voz es una evolución posterior del mini-chat, no un requisito inicial.

Debe poder:
- iniciar una consulta hablada sobre la tarjeta;
- transcribir el comando y mostrar qué entendió;
- permitir corregir la transcripción antes de actuar cuando haya ambigüedad;
- leer una respuesta cuando el usuario lo solicite.

La voz no debe ejecutar acciones silenciosamente. Los comandos que escriban datos deben pasar por el mismo flujo de propuesta y aprobación que el chat.

## 5. Capacidades y permisos

Separar tres capacidades:
1. **Consultar:** leer y analizar únicamente el contexto autorizado.
2. **Proponer:** generar un borrador, informe, artefacto o cambio sugerido.
3. **Operar:** ejecutar una acción aprobada mediante herramientas tipadas de LifeOS/Mind.

Por defecto, el Orbe puede consultar y proponer dentro del contexto concedido. No puede modificar contenido canónico ni crear tareas sin aprobación explícita.

## 6. Flujo obligatorio de operaciones

1. El usuario formula una solicitud desde la tarjeta o selección.
2. El Orbe declara/respeta el contexto autorizado.
3. Interpreta la intención y prepara una propuesta.
4. Muestra una vista previa precisa: qué se creará, cambiará o eliminará.
5. El usuario puede editar, aprobar o rechazar.
6. Solo lo aprobado se ejecuta mediante la API/servicio canónico.
7. El sistema devuelve el resultado verificable y registra la operación.

Una respuesta conversacional nunca debe afirmar que una tarea, documento o modificación quedó creada sin confirmación del sistema.

## 7. Artefactos

Los Orbes podrán producir resúmenes, informes, tablas, gráficos, mapas conceptuales, planes, checklists y propuestas. Los artefactos:
- tienen identidad propia;
- conservan autoría/Orbe, fecha, fuentes y contexto;
- pueden guardarse como contenido canónico y mostrarse como tarjeta;
- pueden moverse, editarse, conectarse y reutilizarse;
- declaran fórmula, fuente, unidad y período cuando contienen métricas.

Los artefactos no deben inventar datos ni convertirse automáticamente en acciones ejecutables.

## 8. Sesiones

Se conserva la posibilidad de:
- **Orbes temporales:** resuelven una tarea puntual; el usuario decide qué artefactos guardar.
- **Orbes persistentes:** conservan conversación, decisiones, contexto y referencias para investigación o proyectos de largo plazo.

Cerrar una sesión no elimina automáticamente el contenido fuente ni los artefactos guardados.

## 9. Arquitectura conceptual

Mantener separados:
- Orbe: interfaz/sesión contextual;
- rol de agente: objetivo e instrucciones;
- modelo/proveedor: motor intercambiable;
- contexto: fuentes y permisos;
- herramientas: operaciones tipadas;
- artefactos: resultados persistibles;
- propuestas: cambios pendientes;
- aprobación: decisión explícita;
- ejecución: operación trazable.

No diseñar Mind alrededor de un proveedor o modelo específico.

## 10. Etapas futuras

- **Orbe v1 — mini-chat contextual de solo lectura:** consulta, explicación, resumen y referencias sobre una tarjeta.
- **Orbe v2 — artefactos y propuestas:** informes, planes, listas y propuestas de creación/edición con preview y aprobación.
- **Orbe v3 — voz y herramientas:** comandos de voz, creación de tareas y otras operaciones canónicas mediante herramientas tipadas y confirmación.
- **Orbe v4 — continuidad avanzada:** sesiones persistentes, contexto ampliable y múltiples roles/agentes cuando exista una necesidad demostrada.

No construir todavía agentes autónomos, cadenas multiagente, ejecución en segundo plano, memoria global sin límites ni acciones externas.
