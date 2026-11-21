# Orbes — Modelo funcional

**Versión:** 0.1 · **Estado:** concepto acordado; sin implementación autorizada.

## 1. Definición
Un Orbe es una instancia de interacción inteligente vinculada a un contexto de Mind. Se presenta como un minichat contextual y un espacio de trabajo capaz de analizar información, colaborar con el usuario, producir artefactos y proponer operaciones sobre el Canvas.

Un Orbe no es sinónimo de modelo, agente ni proveedor. Es la experiencia/sesión contextual que puede utilizar uno o varios roles de agente, modelos y herramientas.

## 2. Ámbito de vinculación
- **Orbe de objeto:** trabaja sobre una nota, idea, recurso o entidad individual.
- **Orbe de grupo:** trabaja sobre un conjunto seleccionado de elementos y sus relaciones.
- **Orbe de espacio:** trabaja sobre el contexto autorizado de un Space o Canvas.

La invocación debe dejar claro qué elementos y fuentes están incluidos.

## 3. Persistencia híbrida
### Persistente
- Conserva conversación, historial, contexto, referencias y artefactos.
- Puede retomarse posteriormente.
- Adecuado para investigaciones, proyectos y líneas de pensamiento de largo recorrido.

### Temporal
- Se crea para una tarea puntual.
- No exige conservar una sesión conversacional permanente.
- Los artefactos que el usuario decida guardar sobreviven al cierre.
- Debe quedar trazabilidad suficiente sobre origen y contexto de los resultados guardados.

Cerrar o eliminar una sesión no elimina automáticamente sus artefactos ni el contenido fuente.

## 4. Contexto híbrido
Cada Orbe comienza con un contexto explícito: objeto, selección, grupo, Canvas o Space. Puede solicitar ampliar o actualizar ese contexto.

La ampliación presenta:
- elementos/fuentes que quiere incorporar;
- motivo y relación con la tarea;
- alcance de lectura solicitado;
- consecuencias sobre la interpretación previa.

El usuario autoriza o rechaza la ampliación. No existe acceso global implícito a todo Mind.

Distinguir:
- **contexto fijado:** snapshot de las fuentes usadas para una tarea o análisis reproducible;
- **contexto vivo:** referencias autorizadas que pueden reflejar cambios posteriores;
- **contexto ampliado:** nuevas fuentes aceptadas por el usuario.

Los artefactos analíticos deben indicar si reflejan un snapshot o datos vivos y cuándo fueron generados.

## 5. Autonomía y permisos híbridos
Existe una política global de permisos y límites. Cada Orbe puede tener configuración particular más restrictiva o especializada, pero nunca superar el techo global.

Capacidades:
1. **Observar:** leer fuentes autorizadas, buscar, analizar y relacionar.
2. **Proponer:** preparar artefactos, conexiones, reorganizaciones o cambios.
3. **Operar:** aplicar una propuesta aprobada a través de herramientas tipadas.

Por defecto:
- lectura limitada al contexto autorizado;
- generación de respuestas y propuestas permitida;
- modificaciones de Canvas o entidades canónicas requieren preview y aprobación explícita;
- operaciones externas o sensibles requieren permisos y confirmación específicos.

La aprobación debe describir exactamente qué cambiará. El usuario puede editar, aprobar o rechazar una propuesta.

## 6. Ciclo de trabajo
1. **Invocar:** desde un objeto, grupo, Space/Canvas o entrada global.
2. **Declarar contexto:** mostrar fuentes incluidas y límites.
3. **Interactuar:** conversación de tarea con referencias al material.
4. **Ampliar:** solicitar autorización cuando falte contexto.
5. **Producir:** generar respuesta o artefactos tipados.
6. **Proponer operación:** mostrar cambios sobre Canvas/datos con vista previa.
7. **Aprobar/aplicar:** ejecutar únicamente el conjunto aprobado.
8. **Continuar o cerrar:** conservar sesión persistente o cerrar sesión temporal; guardar artefactos por separado.

## 7. Artefactos
Tipos iniciales candidatos:
- resumen;
- informe;
- gráfico;
- tabla;
- mapa conceptual;
- plan;
- lista de hallazgos;
- propuesta de conexiones;
- propuesta de reorganización del Canvas.

Cada artefacto conserva:
- ID y tipo;
- contenido estructurado y representación;
- Orbe de origen;
- fuentes y contexto utilizados;
- fecha de generación;
- fórmula, unidad, período y limitaciones cuando aplique;
- estado (borrador, aceptado, descartado, desactualizado) cuando corresponda.

Los artefactos pueden ser nodos en Canvas, pero siguen siendo objetos con identidad propia. Un artefacto no debe afirmar que una operación se ejecutó hasta recibir confirmación del sistema.

## 8. Operaciones sobre Canvas y LifeOS
El Orbe puede preparar operaciones como:
- agregar nodos o grupos;
- proponer conexiones visuales/semánticas;
- reorganizar posiciones;
- crear una nueva nota/idea;
- preparar tareas o cambios de proyecto cuando exista integración autorizada.

Flujo obligatorio: propuesta → preview/diff → aprobación explícita → ejecución mediante API/herramientas tipadas → resultado verificable.

Mover o agrupar nodos no debe modificar el contenido canónico. Borrar contenido canónico requiere una confirmación separada y explícita.

## 9. Memoria y continuidad
La memoria de una sesión persistente no equivale a acceso ilimitado. Debe conservar referencias, decisiones, artefactos y contexto necesario, con controles para revisar y limitar fuentes. Los Orbes temporales no retienen una memoria conversacional permanente por defecto.

No definir todavía una memoria semántica global compartida entre todos los Orbes. El aislamiento entre sesiones es la opción inicial más segura.

## 10. Costos y proveedores
- Modelo y proveedor son intercambiables.
- La elección puede considerar calidad, latencia, disponibilidad, privacidad y costo.
- Registrar modelo/proveedor, tarea, consumo/costo disponible y resultado sin almacenar datos sensibles innecesarios.
- No diseñar el producto alrededor de una marca de modelo.

## 11. Arquitectura conceptual
| Componente | Responsabilidad |
|---|---|
| Orbe | Sesión/UI contextual |
| Agent role | Instrucciones, objetivo y capacidades |
| Model | Motor de inferencia |
| Tools | Operaciones tipadas permitidas |
| Context | Fuentes y permisos |
| Artifact | Resultado reutilizable |
| Proposal | Cambio pendiente de aprobación |
| Approval | Decisión explícita del usuario |
| Run | Ejecución trazable |

No se requiere un agente/modelo distinto por cada Orbe. Un Orbe puede usar distintos roles según la tarea.

## 12. MVP futuro de Orbes
No forma parte del primer MVP de Mind. Cuando se autorice, comenzar con un Orbe sencillo:
1. invocación sobre un objeto o selección;
2. contexto explícito y visible;
3. conversación de una tarea;
4. respuesta con referencias;
5. generación de un artefacto simple;
6. propuesta de una única operación de Canvas;
7. preview y aprobación;
8. registro del resultado.

Persistencia avanzada, varios agentes, automatización en segundo plano y acciones externas quedan fuera de la primera implementación.
