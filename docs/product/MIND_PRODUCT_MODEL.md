# Mind — Modelo de producto

**Versión:** 0.1 · **Estado:** dirección de producto acordada; implementación no autorizada.

## 1. Propósito
Mind es el entorno de pensamiento y conocimiento de LifeOS. Permite capturar información sin fricción, explorar ideas, investigar, aprender, construir mapas visuales y transformar información dispersa en conocimiento y artefactos reutilizables.

Principio rector: el usuario piensa; Mind ayuda a explorar y organizar; los Orbes colaboran; el usuario decide.

Mind no debe convertirse en un gestor de tareas disfrazado, un simple pizarrón infinito ni una interfaz de chat que reemplace el conocimiento estructurado.

## 2. Pilares
1. **Capture / Inbox:** registrar pensamientos, preguntas, notas, enlaces y recursos con mínima fricción. Una captura puede permanecer sin clasificar.
2. **Spaces:** contextos flexibles como Personal, Research o Learning. Agrupan canvases y conocimiento, pero no aíslan ni duplican contenido.
3. **Canvas:** lienzo libre e infinito como entorno visual de exploración. La estructura es opcional y evoluciona con el usuario.
4. **Knowledge:** notas, ideas, conceptos, fuentes, aprendizajes y relaciones reutilizables.
5. **Orbes:** minichats inteligentes asociados a un objeto, grupo o espacio, capaces de analizar y producir artefactos contextuales.
6. **Insights:** hallazgos y conexiones sobre el conocimiento. No reemplazan Analytics, que mantiene las métricas longitudinales del desempeño personal.

## 3. Organización conceptual
- Mind tiene una Inbox transversal para capturas pendientes.
- El usuario puede crear y abrir varios Spaces.
- Cada Space puede contener uno o más Canvases y una biblioteca de conocimiento.
- Un mismo contenido puede referenciarse desde varios Canvases sin duplicarse.
- La captura rápida debe estar disponible desde cualquier contexto.
- Crear contenido dentro de un Canvas puede asignarle ese contexto inicial sin obligarlo a pasar por Inbox.

## 4. Canvas y contenido
Separar tres capas:

### Contenido canónico
Ideas, notas, recursos y entidades LifeOS. Conservan identidad, contenido, metadatos y relaciones propias.

### Representación visual
CanvasNode representa visualmente un contenido o elemento. Guarda referencia al contenido canónico, posición, tamaño, estilo y estado visual. El nodo no es el contenido.

### Relaciones
Las conexiones visuales representan líneas entre nodos. Las relaciones semánticas representan significado y sobreviven a cambios de posición. Una línea visual puede no tener semántica; una relación semántica puede representarse en varios canvases.

Reglas:
- Mover un nodo cambia solo su posición.
- Quitar un nodo de un Canvas elimina la representación, no el contenido original.
- Eliminar contenido canónico requiere confirmación y afecta sus referencias.
- Editar contenido actualiza todas sus representaciones.
- Una nota puede aparecer en varios canvases con posiciones independientes.
- Los elementos puramente visuales (texto libre, formas, grupos) no necesitan convertirse en entidades de dominio.

## 5. Creación de elementos
El usuario puede elegir entre:
- **Contenido:** idea, nota, recurso.
- **Entidades LifeOS:** objetivo, proyecto, tarea, hábito.
- **Elementos visuales:** texto, forma, grupo.

Las entidades LifeOS se crean mediante sus módulos/servicios canónicos, nunca mediante una segunda implementación paralela dentro del Canvas. No todos los tipos estarán disponibles en el primer MVP.

## 6. Relaciones semánticas
Tipos iniciales candidatos:
- relacionado con;
- parte de;
- depende de;
- contribuye a;
- evidencia de;
- contradice;
- desarrolla.

Debe existir también la posibilidad de dibujar una conexión puramente visual sin asignarle un significado formal.

## 7. Búsqueda
- Búsqueda global sobre contenido de Mind y, progresivamente, entidades vinculadas de LifeOS.
- Búsqueda contextual dentro del Space/Canvas actual, con filtros.
- Un resultado puede abrir el contenido original, navegar hasta una representación en un Canvas o agregar una referencia a otro Canvas sin duplicar el contenido.

## 8. Orbes
El comportamiento completo está definido en `docs/product/ORBES_MODEL.md`. Resumen de decisiones acordadas:
- Orbes de objeto, grupo y espacio.
- Persistencia híbrida: Orbes persistentes conservan sesión/historial/contexto; Orbes temporales resuelven una tarea puntual. Los artefactos útiles sobreviven al cierre de una sesión temporal.
- Contexto híbrido: contexto inicial explícito, ampliable con autorización.
- Permisos híbridos: política global y permisos particulares por Orbe, sin exceder los límites globales.
- Observar y proponer son capacidades distintas de operar. Cambios en Canvas o datos canónicos requieren preview y aprobación.
- Orbes no son modelos ni agentes: son instancias de interacción/contexto que pueden coordinar roles, modelos y herramientas.

## 9. Artefactos
Los Orbes pueden producir informes, resúmenes, gráficos, métricas, mapas, planes, listas de hallazgos y otros resultados tipados. Un artefacto:
- tiene identidad propia y tipo;
- conserva referencia a su fuente y al Orbe que lo produjo;
- declara período, fórmula y fuente cuando contiene métricas;
- puede visualizarse en el Canvas, moverse, expandirse, conectarse, editarse y reutilizarse;
- no se convierte automáticamente en una entidad de dominio o acción ejecutable.

Las métricas siempre deben derivarse de datos reales. Prohibido inventar series, resultados, salud o progreso.

## 10. Límites entre Mind y Analytics
Mind puede analizar contenido y datos dentro de un contexto, generar visualizaciones y reportes puntuales. Analytics es responsable del catálogo oficial, fórmulas canónicas e historial del desempeño personal. Un artefacto generado por un Orbe debe reutilizar métricas oficiales cuando existan y declarar cualquier cálculo ad hoc.

## 11. No objetivos
- Forzar que cada captura se convierta en tarea/proyecto.
- Duplicar las entidades de LifeOS.
- Convertir cada relación visual en una relación semántica.
- Ejecutar cambios canónicos sin aprobación.
- Construir una red multiagente compleja antes de validar el uso de un Orbe simple.
- Hacer que Mind dependa de un proveedor o modelo específico.
- Incorporar servicios remotos por defecto.

## 12. MVP candidato — todavía por especificar
1. Crear Space y Canvas.
2. Crear ideas y notas.
3. Posicionar, mover y conectar nodos.
4. Reabrir/editar contenido canónico desde el Canvas.
5. Mantener referencias a un mismo contenido en varios canvases.
6. Guardar y restaurar el estado del lienzo.
7. Captura rápida en Inbox.
8. Exportación/backup y comportamiento offline coherentes.

Los Orbes reales, los artefactos generados por IA y las operaciones asistidas se planifican como una etapa posterior. El MVP debe ser útil sin IA.

## 13. Decisiones pendientes
- Esquema exacto de Spaces, Canvases, nodos, conexiones y contenido.
- Modelo de persistencia y migración compatible con SQLite/Alembic.
- Interacción de Canvas en móvil y estrategia de accesibilidad.
- Límites de rendimiento y virtualización para canvases grandes.
- Versionado, exportación, referencias rotas y borrado.
- Catálogo inicial de artefactos y formatos.
- Contexto, memoria, retención y aislamiento de sesiones Orbe.
- Selección de proveedores/modelos y política de costos.

Estas decisiones requieren diseño y aprobación antes de implementar.
