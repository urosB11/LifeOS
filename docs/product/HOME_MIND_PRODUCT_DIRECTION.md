# Home & Mind — dirección de producto

**Fecha:** 23 de noviembre de 2026  
**Estado:** dirección adoptada para orientar la planificación; no habilita por sí sola implementación.  
**Fuente:** [Propuesta conceptual de UX Home & Mind](research/HOME_MIND_UX_PROPOSAL.md).

## 1. Modelo de producto

LifeOS ofrece tres modos complementarios:

| Modo | Superficie | Pregunta central | Verbo |
|---|---|---|---|
| **Orientación** | Home | ¿Qué necesita mi atención? | Leer, decidir |
| **Gestión** | Tasks, Projects, Habits, Notes | ¿Qué tengo que crear, modificar, completar o registrar? | Actuar |
| **Pensamiento** | Mind | ¿Cómo se conecta esto con lo demás y cómo puedo desarrollarlo? | Explorar, conectar, construir |

Home es síntesis operativa, no fuente de verdad. Los módulos mantienen los datos canónicos. Mind es el entorno visual para pensamiento y trabajo profundo; no es un gestor duplicado ni una aplicación de notas genérica.

**Principio central: un dato, una fuente de verdad y múltiples representaciones.**

## 2. Decisiones de producto D1–D5

Estas decisiones cierran la dirección conceptual para planificar las próximas fases. No amplían el alcance de MIND-002 ni convierten MIND-003 en una entrega READY.

### D1 — Captura: dual en la experiencia, conectada en el modelo

**Decisión actual: opción B de la propuesta, dual pero conectada.**

- Home conserva Quick Capture para crear Tasks o Notes mediante los servicios canónicos existentes.
- Mind conserva su Inbox transversal para capturas sin clasificar.
- Una Note creada desde Home no se envía automáticamente al Inbox. No se crean dos modelos de Notes ni copias del contenido.
- Desde Mind, el usuario podrá incorporar explícitamente una Note existente a un Canvas. La acción debe ser explícita y no borrar ni retirar silenciosamente la Note del Inbox.
- La convergencia futura se evaluará después de que Mind y sus integraciones estén estables (MIND-006 o posterior). Convergencia significa reutilizar servicios y mantener una experiencia coherente; no obliga a fusionar prematuramente las interfaces.

### D2 — Notes y Knowledge: conservar Notes ahora; evaluar una vista unificada después

**Decisión actual: opción A; destino a evaluar: opción B.**

- Notes permanece como módulo y acceso de navegación. No se elimina, redirige ni migra durante MIND-003.
- Knowledge se desarrolla como biblioteca de contenido canónico reutilizable en MIND-005.
- Cuando Knowledge y búsqueda estén implementados, evaluar Notes como una vista/acceso a esa biblioteca, preservando IDs, enlaces y contenido. No crear una segunda fuente de verdad.

### D3 — Presencia de Mind en Home: ambos accesos, más adelante

**Decisión: evaluar después de MIND-006 dos widgets opcionales y discretos:**

1. cantidad de capturas pendientes en Mind Inbox;
2. Canvases o Spaces recientes para continuar trabajando.

No se incorporan a MIND-003. Home no contiene un Canvas, no replica Cards y no convierte el contenido de Mind en un segundo panel de gestión. Cada widget deberá enlazar al contexto original y mostrar estados vacíos y errores honestos.

### D4 — Proyecto: Projects sigue siendo el lugar operativo primario

**Decisión actual: opción A; evaluar flexibilidad futura (opción C).**

- Projects conserva CRUD, estado y reglas operativas canónicas.
- Mind puede ofrecer un Canvas como espacio de trabajo complementario de un proyecto cuando exista la integración MIND-006.
- No todos los proyectos necesitan un Canvas. No se duplica Project, Task, Habit ni sus reglas dentro de Mind.
- Evaluar una experiencia de doble entrada solo después de observar el uso real y diseñar transiciones inequívocas.

### D5 — Widgets: catálogo extensible con contrato explícito

- Home debe evolucionar mediante un catálogo controlado de widgets, no mediante una lista cerrada codificada en cada pantalla.
- Un widget necesita contrato definido: identidad, fuente de datos canónica, configuración/visibilidad, acciones permitidas, estados loading/empty/error, comportamiento responsive, accesibilidad y pruebas.
- Mind podrá contribuir widgets oficiales (por ejemplo, Inbox count y Canvases recientes) después de MIND-006 y de definir ese contrato.
- **Una Card de Mind no se convierte automáticamente en un widget de Home.** No se comparte el motor espacial del Canvas con el grid de Home.

## 3. Home y Mind conservan superficies diferentes

Esta distinción es intencional:

- **Home:** grid responsive de widgets, lectura vertical y secuencial, jerarquía operativa, visitas breves.
- **Mind:** Canvas espacial libre, posiciones persistentes, conexiones, exploración no lineal y sesiones de trabajo sostenidas.

No construir un Canvas compartido ni forzar widgets dentro de Mind. La coherencia del producto se consigue compartiendo:

- tokens y lenguaje visual;
- semántica consistente de Guardar, Cancelar, Escape, Enter y confirmación;
- patrones de loading, empty, error y success;
- foco visible, accesibilidad por teclado y alternativas táctiles;
- servicios, IDs y datos canónicos;
- navegación contextual y feedback.

Compartir un componente solo cuando el comportamiento y el contrato sean realmente equivalentes. No crear abstracciones comunes por similitud superficial.

## 4. Implicaciones para MIND-003

MIND-003 sigue siendo **Canvas interactivo y relaciones visuales**, según `MIND_ROADMAP.md`. Esta fase debe profundizar el valor espacial de Mind, no integrar Home y Mind de forma prematura.

- Las conexiones de MIND-003 son visuales y locales a un Canvas. No son relaciones semánticas entre contenidos; estas corresponden a MIND-005.
- MIND-003 debe contemplar selección múltiple, redimensionamiento, orden visual, teclado/touch y undo/redo persistente.
- Agrupaciones o frames se incorporan solo si Mimo demuestra un caso de uso claro y un costo razonable.
- Exponer la acción explícita para añadir una Note existente del Inbox a un Canvas es coherente con la entrega y con el endpoint `attach_note` ya presente. Añadir una representación no duplica el contenido ni retira automáticamente la Note del Inbox.
- Pan, zoom, movimiento de Cards, Notes canónicas y estados ya entregados por MIND-002 se reutilizan y se someten a pruebas de regresión; no se reimplementan sin necesidad.
- No incorporar widgets de Home, búsqueda/Knowledge completa, relaciones semánticas, documentos por bloques, multimedia, Cards vivas de Tasks/Projects/Habits, Orbes, IA ni voz en esta fase.

## 5. Principios compartidos no negociables

1. No duplicar datos canónicos.
2. El usuario decide qué se mueve, clasifica, vincula o elimina.
3. Añadir una representación visual no equivale a mover o borrar el contenido.
4. Un error de red o persistencia nunca se presenta como un estado vacío exitoso.
5. Los borradores se conservan ante fallos y cancelaciones.
6. Cada acción relevante tiene feedback visible y alternativa accesible.
7. Lo espacial persiste; ninguna operación de dominio queda solo en estado efímero del frontend.
8. Mind y Home funcionan sin depender de IA o servicios externos.

## 6. Secuencia de trabajo

1. **Planificación MIND-003:** Opus revisa coherencia UX/producto; Sonnet audita arquitectura; Mimo integra ambas revisiones y finaliza SPEC/HANDOFF.
2. **Gate PO:** revisar SPEC, alcance, dependencias, pruebas, esquema y estrategia de migración. Solo entonces cambiar MIND-003 de PLANNING a READY.
3. **Implementación:** Mimo trabaja en la rama/worktree de Mind, no en Evolution ni en planificación.
4. **QA independiente:** reviewer distinto de Mimo, con pruebas temporales y evidencia visual/interactiva.
5. **Aceptación:** el PO acepta o solicita correcciones; no marcar DONE por autocertificación del agente.

## 7. Riesgo de integración conocido

MIND-002 creó la revisión Alembic `0006_mind`; Evolution creó `0006_home_widget_grid`. El handoff de MIND-002 documenta una estrategia recomendada, pero todavía pendiente de decisión para integrar ambas líneas. La planificación de MIND-003 puede continuar; **ningún agente debe resolver esta colisión, renumerar migraciones o aplicar migraciones a la base personal** sin una decisión explícita y verificación sobre bases temporales.
