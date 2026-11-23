# MIND-003 — Canvas interactivo y relaciones visuales

**Prioridad:** P1
**Estado:** PLANNING — especificación para revisión; no autoriza implementación
**Responsable:** Mimo / Developer
**Dependencia:** MIND-002 (REVIEW; aceptación del PO pendiente)
**Rama de planificación:** `planning/mind-001`
**Fecha:** 23 de noviembre de 2026

> Esta SPEC consolida la dirección aprobada, la guía del PO y las capacidades comprobadas de MIND-002. No se encontraron los informes de revisión de Opus ni Sonnet: sus conclusiones no se presumen ni se atribuyen a este documento. La revisión de ambos y la aceptación del PO siguen siendo gates antes de pasar a READY.

## 1. Objetivo

Permitir que el usuario organice, conecte y manipule Cards de Notes en el Canvas existente, y que esos cambios espaciales sobrevivan recargas, errores recuperables, exportación y restauración. El Canvas sigue siendo una superficie libre de pensamiento; no se convierte en un gestor de dominio ni en un segundo sistema de Notes.

## 2. Scope Baseline

- **Discovery method:** dirección Home–Mind y D1–D5, modelo y roadmap Mind, guía del PO, SPEC/HANDOFF de MIND-002 e inspección read-only de su implementación. La propuesta UX es insumo, no autoridad para ampliar alcance.
- **Unidad de entrega:** una extensión del Canvas de MIND-002, sin rehacerlo ni alterar Home.
- **Items discovered:** 10 áreas requeridas por la guía del PO y una opción explícitamente condicional (Frames).
- **Items in scope:** las 10 áreas requeridas; Frames quedan fuera hasta revisión UX y arquitectónica.
- **Capacidades incluidas:** representar Notes existentes, conexiones visuales locales, multi-selección, movimiento grupal, resize, orden, undo/redo persistente, accesibilidad/touch y ciclo de export/backup/restore.
- **Datos canónicos:** Notes existentes; no se añade una entidad de contenido duplicada.
- **Datos nuevos previstos:** conexiones visuales y un historial acotado necesario para undo/redo; el historial no es una fuente de verdad de dominio.
- **Estado de revisión:** los informes de Opus y Sonnet no están disponibles; esta línea base queda sujeta a sus observaciones y a revisión del PO.

## 3. Autoridad y decisiones de producto

Prevalecen `HOME_MIND_PRODUCT_DIRECTION.md`, `MIND_PRODUCT_MODEL.md`, `MIND_ROADMAP.md`, esta guía y la línea base de MIND-002. La propuesta UX de Home–Mind informa el diseño, pero no amplía por sí sola el alcance.

- **D1 — Captura:** Home y Mind mantienen experiencias distintas. MIND-003 permite añadir explícitamente una Note existente a un Canvas; no la envía automáticamente al Inbox ni la retira de él.
- **D2 — Notes:** Notes conserva su módulo, sus IDs y su contenido canónico. No se duplica, migra ni sustituye.
- **D3 — Home:** no se agregan widgets de Mind, Cards ni Canvas a Home.
- **D4 — Projects:** Projects, Tasks y Habits no se representan como Cards vivas ni se gestionan desde MIND-003.
- **D5 — Widgets:** no se cambia el catálogo ni el motor de Home. No se comparte el motor espacial de Canvas con el grid de Home.

Una **conexión visual** es una línea entre dos instancias de Cards en el mismo Canvas. Es local a ese Canvas, no tiene tipo, etiqueta ni dirección, y no expresa ni crea una relación de dominio. Una **relación semántica** conecta contenido canónico independientemente de su ubicación y pertenece a MIND-005. MIND-003 no crea ni modifica relaciones semánticas.

## 4. Alcance

### 4.1 Incluido

- Reutilizar pan, zoom, drag, edición de Notes y navegación de MIND-002.
- Añadir al Canvas una Note existente mediante una acción explícita. La Note mantiene su membresía en Inbox y su contenido canónico.
- Crear y quitar conexiones visuales locales entre Cards.
- Seleccionar varias Cards y moverlas como una sola operación atómica.
- Redimensionar una Card, con persistencia en coordenadas del mundo.
- Cambiar y persistir el orden de apilamiento.
- Deshacer y rehacer operaciones espaciales después de recargar la aplicación.
- Teclado, lectores de pantalla, mouse, touch, estados de error y respuesta responsive.
- Incorporar las conexiones a export JSON, backup SQLite y restauración con integridad referencial.
- Probar la migración sobre bases temporales con datos MIND-002; no sobre la base personal.

### 4.2 Fuera de alcance

- Relaciones semánticas, tipos o etiquetas de relaciones, Knowledge y búsqueda global o contextual (MIND-005).
- Nuevos tipos de Card, documentos por bloques, editor rico o cambios al modelo de Notes (MIND-004).
- Cards vivas de Tasks, Projects o Habits e integración operativa (MIND-006).
- Frames persistentes, grupos anidados, alineación/distribución, plantillas y automatización de layout. La selección múltiple es transitoria y no crea una entidad de grupo.
- Home, su catálogo, su grid y su persistencia de widgets.
- IA, Orbes, voz, llamadas externas, colaboración, sincronización cloud o telemetría.
- Librerías/frameworks de Canvas, dependencias runtime nuevas y cambios a Evolution.
- Eliminar una Note como acción de Canvas. La eliminación canónica continúa en Notes, con su confirmación existente.

Frames solo podrán incorporarse mediante una revisión explícita de esta SPEC si Opus identifica un caso de uso y Sonnet confirma su costo y límites. No son un supuesto para implementar.

## 5. User Scenarios & Testing

### Historia 1 — Llevar una Note existente al Canvas (P1)

Como usuario, quiero colocar en un Canvas una Note capturada en el Inbox sin moverla ni copiarla, para pensarla en contexto y conservar su acceso original.

**Prueba independiente:** seleccionar una Note del Inbox, añadirla a un Canvas y comprobar su contenido e Inbox después de recargar.

1. **Dado** que una Note está en el Inbox, **cuando** el usuario elige “Añadir al Canvas” y selecciona un Canvas, **entonces** se crea una representación que referencia el mismo ID de Note y la membresía del Inbox permanece.
2. **Dado** que la Note ya está representada en ese Canvas, **cuando** se intenta añadirla otra vez, **entonces** no se duplica y se ofrece ir a la Card existente.
3. **Dado** que esa Note existe en otro Canvas, **cuando** el usuario la añade aquí, **entonces** se crea una representación independiente que comparte la Note canónica.

### Historia 2 — Conectar Cards visualmente (P1)

Como usuario, quiero dibujar y quitar líneas entre Cards para expresar una organización visual propia sin cambiar el significado ni los datos de las Notes.

**Prueba independiente:** crear una conexión, recargar, comprobar sus extremos y quitarla; ninguna Note ni membresía cambia.

1. **Dado** dos Cards del mismo Canvas, **cuando** el usuario confirma “Conectar con…” o completa el gesto de conexión, **entonces** aparece una línea persistida entre ellas.
2. **Dado** que una conexión existe, **cuando** cualquiera de sus extremos se mueve, redimensiona o reordena, **entonces** la línea sigue unida a las Cards.
3. **Dado** que una conexión está seleccionada, **cuando** el usuario la quita, **entonces** desaparece y puede recuperarse con Deshacer.

### Historia 3 — Organizar una selección (P1)

Como usuario, quiero seleccionar varias Cards, moverlas juntas, cambiar el tamaño de una Card y ajustar su orden, para reorganizar el espacio sin perder la disposición al volver.

**Prueba independiente:** seleccionar dos Cards, moverlas juntas, redimensionar otra, cambiar su orden, recargar y verificar posición, tamaño y apilamiento.

1. **Dado** un Canvas con varias Cards, **cuando** el usuario las selecciona y las mueve, **entonces** se conserva su distancia relativa y el conjunto se persiste como una acción.
2. **Dado** una Card enfocada, **cuando** se redimensiona con mouse, teclado o touch, **entonces** conserva un tamaño válido y su contenido sigue siendo accesible.
3. **Dado** varias Cards superpuestas, **cuando** se usa “Traer al frente” o “Enviar atrás”, **entonces** el orden resultante es persistente y determinista.

### Historia 4 — Deshacer y rehacer (P1)

Como usuario, quiero revertir o repetir una acción espacial incluso después de recargar, para explorar una organización sin perder control.

**Prueba independiente:** hacer una operación espacial, recargar, deshacerla, recargar de nuevo y rehacerla; ambas posiciones deben coincidir con el estado antes y después de la acción original.

1. **Dado** un cambio guardado, **cuando** el usuario elige Deshacer, **entonces** se restaura el estado anterior completo de esa acción.
2. **Dado** un cambio deshecho, **cuando** el usuario elige Rehacer, **entonces** se reaplica el mismo estado.
3. **Dado** que se deshizo una acción, **cuando** se guarda una acción nueva, **entonces** la rama de rehacer anterior deja de estar disponible.

### Historia 5 — Usar Canvas con teclado y touch (P1)

Como usuario, quiero completar selección, conexión, movimiento, resize y orden sin depender de un gesto de arrastre preciso, para trabajar con distintos dispositivos y tecnologías de asistencia.

**Prueba independiente:** completar las operaciones principales por teclado y en un viewport táctil, sin pérdida de foco, controles fuera de alcance ni overflow horizontal.

1. **Dado** que el usuario navega Cards con Tab, **cuando** inicia una conexión desde la acción accesible y elige un destino, **entonces** la conexión se crea sin arrastrar ni perder el foco.
2. **Dado** que el usuario está en un dispositivo táctil, **cuando** activa Seleccionar y marca Cards, **entonces** puede mover la selección y cancelar una interacción con Escape o el control Cancelar.
3. **Dado** que una operación espacial no se pudo guardar, **cuando** el usuario vuelve a intentar o cancela, **entonces** ve el estado pendiente y no recibe una confirmación de guardado falsa.

## 6. Requirements

### Functional Requirements

- **REQ-001:** El usuario debe poder añadir explícitamente a un Canvas una Note existente, conservando el mismo ID canónico y su membresía original del Inbox.
- **REQ-002:** El sistema debe impedir una segunda representación de la misma Note en el mismo Canvas y permitir representar esa Note en otros Canvases.
- **REQ-003:** El usuario debe poder crear, listar y quitar una conexión visual no dirigida entre dos Cards del mismo Canvas, sin tipo, etiqueta ni semántica de dominio.
- **REQ-004:** El sistema debe rechazar auto-conexiones, pares duplicados y referencias a nodos de otro Canvas, sin dejar cambios parciales.
- **REQ-005:** El usuario debe poder seleccionar varias Cards y moverlas conservando sus offsets; el grupo se guarda como una acción atómica.
- **REQ-006:** El usuario debe poder redimensionar una Card dentro de los límites definidos, con previsualización y un solo guardado por interacción completa.
- **REQ-007:** El usuario debe poder cambiar el orden de apilamiento mediante controles explícitos y restaurarlo al reabrir el Canvas.
- **REQ-008:** El usuario debe poder deshacer y rehacer las operaciones espaciales admitidas después de recargar; cada acción de grupo ocupa un solo paso.
- **REQ-009:** Una acción nueva después de Deshacer debe descartar el futuro de Rehacer; el historial conserva hasta 100 acciones por Canvas y se recorta transaccionalmente.
- **REQ-010:** Si se elimina canónicamente una Note, el sistema debe invalidar el historial de los Canvases afectados antes de que pueda restaurar una referencia inexistente; no debe borrar el historial de Canvases no afectados.
- **REQ-011:** Los cambios espaciales, el registro de undo/redo y el evento de actividad asociado deben confirmarse o revertirse en una sola transacción.
- **REQ-012:** El retry de una acción con el mismo `operation_id` no debe duplicar el efecto ni el registro de historial.
- **REQ-013:** La interfaz debe distinguir carga, vacío, guardado, error y borrador pendiente; un fallo nunca se presenta como Canvas vacío ni como guardado exitoso.
- **REQ-014:** Las conexiones y geometría deben incluirse en el export JSON versionado; una importación portable inicia con historial vacío.
- **REQ-015:** El backup/restauración SQLite debe conservar conexiones, IDs, integridad referencial e historial; la migración debe admitir una base vacía y una base MIND-002.
- **REQ-016:** El Canvas debe permitir selección, conexión, movimiento, resize, orden y undo/redo por teclado con foco visible y sin interceptar la edición de texto.
- **REQ-017:** Las conexiones deben tener una alternativa accesible al arrastre y cada relación visual debe poder consultarse sin depender de un SVG o de la percepción visual.
- **REQ-018:** Las acciones esenciales deben tener targets táctiles de al menos 44 × 44 CSS px y no depender de hover ni de un gesto único.
- **REQ-019:** El Canvas debe funcionar en 1440×900, 768×1024 y 390×844, sin overflow horizontal, conservando una alternativa explícita para distinguir pan y selección.
- **REQ-020:** MIND-003 debe reutilizar Notes, los datos y las interacciones de MIND-002; no debe añadir tipos de Cards, entidades canónicas, Frames persistentes, integración Home, IA, dependencias runtime o cambios a Evolution.

### Key Entities

- **MindCanvasNode:** representación visual existente de una Note, con posición, tamaño, orden y referencia canónica.
- **MindCanvasEdge:** conexión visual no dirigida entre dos nodos del mismo Canvas; no expresa una relación semántica.
- **MindCanvasHistoryEntry:** comando espacial reversible con estado anterior/posterior acotado y referencias a las Notes necesarias para invalidarlo de forma segura.
- **Note:** contenido canónico existente; no se duplica ni forma parte del estado espacial.

## 7. Success Criteria

### Measurable Outcomes

- **SC-001:** En pruebas de alta de Note, el ID y el contenido canónico permanecen iguales antes y después de añadirla al Canvas; la membresía de Inbox no cambia.
- **SC-002:** En pruebas de Canvas, cada movimiento, resize, orden o conexión confirmados reaparecen iguales después de cerrar y volver a abrir la vista.
- **SC-003:** Las 100 acciones retenidas más recientes pueden deshacerse/rehacerse en el orden documentado, incluso después de recargar; las acciones anteriores al límite ya no están disponibles.
- **SC-004:** Una acción inválida de grupo o conexión produce cero cambios parciales en nodos, conexiones, historial y eventos.
- **SC-005:** El paquete JSON nuevo restaura todas las conexiones y geometría con IDs válidos, mientras que un paquete previo sin conexiones se restaura con cero conexiones y sin error.
- **SC-006:** En las tres dimensiones de viewport requeridas y cada tema disponible no hay overflow horizontal y todas las acciones esenciales se pueden completar por teclado y touch.

## 8. Arquitectura y capacidades existentes

### 8.1 Reutilizar MIND-002

- La fuente canónica del contenido sigue siendo `notes`; `mind_canvas_nodes` representa una Note y conserva posición/tamaño/orden visual.
- El modelo existente ya tiene `width`, `height` y `z_index`; no se agrega otro estado ni una tabla para esos atributos.
- El servicio existente permite añadir una Note con `attach_note` y evita una segunda representación de esa Note dentro del mismo Canvas. La misma Note puede representarse en Canvas distintos.
- Se conservan las coordenadas del mundo, pan, zoom, movimiento de una Card, editor de Note, estados de guardado y rutas actuales.
- El frontend sigue siendo JavaScript/DOM/SVG nativo. El Canvas de Mind no reutiliza el grid de Home.

### 8.2 Extensiones de MIND-003

- Un overlay SVG decorativo renderiza las conexiones y queda debajo de las Cards. No intercepta interacciones de las Cards. Se recalcula visualmente tras pan, zoom, movimiento, resize, cambio de orden y carga.
- Un servicio de comandos del Canvas valida y persiste cada acción espacial en backend. La interfaz puede mostrar una previsualización, pero el backend y SQLite son la fuente de verdad.
- Las operaciones de selección múltiple se envían y guardan como una transacción; no se realizan escrituras por frame.
- Toda mutación espacial, incluida conexión y eliminación visual de una Card, pasa por el mismo registro de historial. No se implementa event sourcing.

## 9. Modelo de datos y persistencia

### 9.1 Datos canónicos y estado del Canvas

`Note` conserva título y cuerpo. `mind_canvas_nodes` conserva la representación, incluido `note_id`, `canvas_id`, `x`, `y`, `width`, `height` y `z_index`. Las posiciones y dimensiones se miden en coordenadas del mundo, sin depender del viewport o del zoom.

“Quitar del Canvas” elimina solo la representación. “Eliminar Note” sigue siendo una acción canónica separada y confirmada; no se añade un borrado de Notes a las operaciones espaciales.

### 9.2 Conexiones visuales

Crear `mind_canvas_edges` con identidad estable, `canvas_id`, IDs de ambos nodos y timestamp. Un índice único sobre `(canvas_id, id)` de nodos permite que dos FKs compuestas exijan que ambos extremos pertenezcan al mismo Canvas. La tabla:

- exige dos nodos existentes pertenecientes al Canvas indicado; el servicio valida la pertenencia y la integridad SQL la refuerza;
- prohíbe conectar una Card consigo misma;
- normaliza el par de IDs al guardar y permite como máximo una conexión no dirigida por par dentro del Canvas;
- elimina conexiones por cascada al borrar un Canvas o una representación;
- no guarda `edge_type`, `label`, `direction`, estilo semántico, contenido de Note ni campos de IA.

La conexión es dato visual independiente de las Notes. Quitarla nunca elimina ni modifica sus extremos.

### 9.3 Historial persistente de undo/redo

Crear `mind_canvas_history` y `mind_canvas_history_note_refs` para que Deshacer/Rehacer funcione después de reiniciar o recargar:

- cada acción confirmada registra tipo, secuencia, `operation_id`, estado anterior y posterior de los nodos/conexiones afectados, estado aplicado y timestamp. `operation_id` es el valor de `Idempotency-Key`; `UNIQUE(canvas_id, operation_id)` hace idempotente el retry y `UNIQUE(canvas_id, sequence)` ordena el historial;
- una acción de grupo produce una única entrada. El registro guarda IDs y estado espacial, nunca el cuerpo de Notes;
- Deshacer elige la acción aplicada de secuencia más alta; Rehacer, la acción deshecha de secuencia más baja. Undo/redo actualizan estado aplicado sin crear otra entrada. Una acción nueva después de deshacer elimina las entradas futuras antes de asignar la siguiente secuencia;
- conservar como máximo 100 entradas por Canvas, incluyendo entradas deshechas. El recorte de las más antiguas ocurre dentro de la misma transacción;
- guardar estado actual y entrada de historial en la misma transacción. Error/rollback no deja cambios parciales ni avanza el cursor;
- cada petición de undo/redo identifica la acción esperada del stack. Si un retry llega después de que el stack avanzó, el backend devuelve el estado actual sin aplicar otra acción;
- `mind_canvas_history_note_refs` conserva una fila por par historial/Note citado en sus snapshots e indexa `note_id`. Antes de borrar una Note canónica, borrar el historial de los Canvas afectados en la misma transacción, evitando resucitar referencias inválidas. La confirmación de eliminar Note debe advertir que esa acción limpia undo/redo de esos Canvas; registrar el hecho sin contenido de Note;
- el historial no es la fuente de verdad del dominio ni un event store. `activity_events` conserva solo eventos resumidos de la operación.

Los cambios de título/cuerpo hechos desde Notes no forman parte del historial espacial. Deshacer un alta o quitar una Card restaura/quita únicamente la representación; nunca elimina ni reconstruye el contenido canónico.

### 9.4 Contrato API

Se conservan los endpoints de MIND-002 para listar/crear Cards, actualizar/quitar una representación y añadir una Note existente. Sus mutaciones espaciales deben pasar por el servicio transaccional de historial.

Agregar operaciones equivalentes a:

- `GET /api/v1/mind/canvases/{canvas_id}/edges`: listar conexiones.
- `POST /api/v1/mind/canvases/{canvas_id}/edges`: crear conexión no dirigida.
- `DELETE /api/v1/mind/canvases/{canvas_id}/edges/{edge_id}`: quitar conexión.
- `POST /api/v1/mind/canvases/{canvas_id}/spatial-actions`: persistir un movimiento grupal u otra acción espacial indivisible.
- `GET /api/v1/mind/canvases/{canvas_id}/history`: indicar si Deshacer/Rehacer están disponibles.
- `POST /api/v1/mind/canvases/{canvas_id}/history/undo` y `/redo`: aplicar una acción.

La ruta actual para `attach_note` se conserva; la acción de UI no debe cambiar la membresía del Inbox. Las rutas son una propuesta de contrato, no autorización para implementarlas ahora. Las validaciones y resultados requeridos son:

- validar IDs, propiedad del Canvas, tamaños y operaciones en backend;
- una acción grupal valida todos sus elementos antes de confirmar; cualquier elemento inválido produce rollback completo;
- toda mutación usa un header `Idempotency-Key` estable por intento lógico; una clave repetida no duplica el efecto ni el historial;
- undo/redo reciben el ID de la acción esperada y rechazan con el estado actual si una petición previa ya movió el stack;
- Canvas archivado es de solo lectura hasta restaurarse;
- devolver errores explícitos: inexistente `404`, conflicto de estado/duplicado/pertenencia `409`, entrada inválida `422`. No representar errores como Canvas vacío ni confirmar éxito antes del commit.

## 10. Interacción, accesibilidad y touch

### 10.1 Selección y movimiento

- Click/tap selecciona una Card; `Shift+click` o `Espacio` con la Card enfocada alterna su selección múltiple.
- Arrastrar en el fondo dibuja un rectángulo de selección. En touch, se requiere activar “Seleccionar” antes de dibujarlo; el gesto por defecto del fondo conserva el pan de MIND-002.
- `Ctrl+A`/`Cmd+A` selecciona solo las Cards del Canvas cuando el foco está en el Canvas, nunca dentro de un input, textarea o editor.
- Arrastrar una Card seleccionada mueve el conjunto conservando offsets. La previsualización no escribe a backend; al soltar se guarda una sola acción atómica.
- La selección es transitoria: no se exporta ni se persiste como grupo.

### 10.2 Conexiones

- Mouse puede arrastrar desde un control de conexión de la Card hasta otra Card.
- Una alternativa visible “Conectar con…” permite iniciar la operación, elegir destino de una lista accesible y confirmar con Enter. Escape cancela sin escribir.
- La línea se selecciona con un control accesible; quitarla es reversible y no exige confirmación destructiva.
- El SVG se oculta a lectores de pantalla. Cada Card expone en DOM una lista legible de sus conexiones y controles para navegar a cada extremo.

### 10.3 Resize y orden

- Los handles de resize aparecen en la Card enfocada/seleccionada, no permanentemente en todas las Cards.
- El tamaño mínimo es 200 × 120 unidades del Canvas; el máximo respeta los límites ya admitidos por backend (10 000 × 10 000). El cuerpo puede desplazarse si no entra completo; título y controles permanecen utilizables.
- El resize se previsualiza mientras se arrastra y se guarda una vez al soltar. Por teclado, `Alt+Flechas` cambia el tamaño en pasos de 8 unidades; con `Shift`, en pasos de 40. Se respeta el mínimo/máximo.
- Acciones explícitas “Traer al frente” y “Enviar atrás” ajustan `z_index` de forma determinista. El backend normaliza el orden a una secuencia válida sin colisiones ni desbordamiento.

### 10.4 Teclado, lectores de pantalla y feedback

- El foco es visible y estable al volver a renderizar; una eliminación visual devuelve foco a la Card siguiente o a la barra del Canvas.
- Las Cards exponen nombre accesible basado en su título. Selección, cantidad seleccionada, conexión creada/quitada, guardado, error, deshacer y rehacer se anuncian mediante un estado `aria-live` no intrusivo.
- `Escape` cancela primero la interacción activa (conectar, selección rectangular, mover o resize) sin persistirla; si no hay una operación activa, limpia la selección. No descarta un borrador del editor de Note.
- `Ctrl+Z`, `Ctrl+Y`/`Ctrl+Shift+Z` y los botones Deshacer/Rehacer actúan solo con el foco dentro del Canvas y no interceptan editores de texto.
- El error de guardado conserva la previsualización pendiente y ofrece Reintentar o Cancelar; muestra que el cambio aún no está persistido. No se presenta como guardado.
- Transiciones breves y funcionales respetan `prefers-reduced-motion`.

### 10.5 Touch y responsive

- Targets interactivos, incluido el área táctil de handles, miden al menos 44 × 44 CSS px.
- Se conservan controles visibles de zoom y gesto de pinch. Pan, selección, movimiento, conexión y resize no dependen de hover ni de un gesto único.
- El fondo mantiene pan por un dedo; un modo explícito de selección evita confundir pan con lasso. Mover Cards comienza en un asa/área de cabecera y no en botones o texto editable.
- En 1440×900, 768×1024 y 390×844, Canvas y toolbar no producen overflow horizontal; los contenidos largos siguen siendo alcanzables.

## 11. Undo/redo, errores y eventos

Cada acción guardada (añadir/quitar representación, conexión, mover, mover selección, resize u ordenar) constituye un paso de historial. No se registran frames intermedios. El servidor serializa cambios por Canvas dentro de la transacción de la petición.

Si una operación o su undo/redo falla, el estado persistido y el historial permanecen sin cambios; se informa el motivo y se permite reintentar o cancelar. Un retry conserva el mismo `Idempotency-Key`; undo/redo reenvía el ID de acción esperado. El borrador fallido se conserva durante la sesión, sin prometer que un cambio no guardado sobreviva al cierre de la aplicación.

Registrar un evento resumido por acción confirmada y por undo/redo en la misma transacción que el estado y el historial. No registrar cada frame, texto de Note, cuerpo exportado ni payload completo. La base actual sigue siendo fuente de verdad; los eventos no se usan para reconstruir el Canvas.

## 12. Exportación, backup y restauración

- El export JSON versionado incluye conexiones, referencias a nodos, tamaños y orden de las Cards. No copia Notes: conserva IDs/referencias según el contrato de export existente.
- El formato portable no incluye el historial operativo de undo/redo; una importación JSON inicia con historial vacío. La restauración SQLite desde un backup completo sí conserva las tablas y el historial.
- Incrementar la versión del export conforme a las reglas existentes después de verificar la versión base integrada; no fijar aquí un número que pueda colisionar con cambios de Evolution.
- Validar antes de restaurar: endpoints existentes, ambos dentro del mismo Canvas; sin auto-conexiones ni pares repetidos; Notes y nodos referenciados presentes. Un paquete inválido falla explícitamente y no deja datos parciales.
- Backup/restore conserva IDs, conexiones y relaciones FK. No escribir exportaciones o backups en Git ni transmitirlos externamente.

## 13. Migraciones

La migración de MIND-003 debe agregar la tabla de conexiones, historial y referencias de historial necesarias, índices/constraints de pertenencia al mismo Canvas y compatibilidad de export. No se migra ni altera el contenido de `notes`; no se agregan campos para resize/z-order porque ya existen en MIND-002.

La cadena Alembic sigue bloqueada por la colisión conocida entre `0006_mind` y `0006_home_widget_grid`. Esta planificación no escoge una estrategia de integración, no asigna números de revisión, no edita migraciones existentes y no ejecuta migraciones. Antes de implementar, el PO debe decidir la integración/base; luego se crea una única revisión nueva sobre el HEAD verificado, se actualiza `DATABASE.md` y se prueban upgrade/downgrade en bases temporales vacías y con datos MIND-002. Nunca usar la base personal.

## 14. Pruebas requeridas para la futura implementación

### Backend y datos

- Conexión válida, auto-conexión rechazada, duplicado en ambas orientaciones rechazado y cruce de Canvas rechazado; borrar una representación elimina sus conexiones, no su Note.
- Añadir Note del Inbox conserva membresía e ID; añadirla dos veces al mismo Canvas no crea otro nodo; añadirla en otro Canvas crea otra representación.
- Tamaños límite, actualización de `z_index` y orden determinista.
- Selección grupal: operación válida persiste todas las Cards y una sola entrada de historial; un miembro inválido revierte todo.
- Undo/redo para cada clase de operación, incluida acción grupal; estado y controles sobreviven recarga; acción nueva tras undo elimina redo; 100 últimas acciones respetan el límite.
- Retry con el mismo `Idempotency-Key` no duplica escrituras. Retry de undo/redo con un stack ya avanzado no aplica otra acción. Errores dejan intactos Canvas e historial.
- Borrar Note limpia las conexiones por cascada e invalida historial únicamente en Canvases que la referenciaban; no queda una vía de resucitar la Note.
- Eventos se guardan en la transacción y no contienen cuerpo de Note ni contenido privado.

### Export, backup, restore y migración

- Export/import JSON nuevo conserva IDs, geometría, orden y conexiones, sin copiar texto canónico ni historial operacional.
- Import JSON anterior sin conexiones sigue siendo aceptado y resulta en Canvas sin conexiones.
- Backup/restore SQLite conserva nodos, conexiones, historial, IDs y FKs; validar con base temporal.
- Upgrade desde la revisión integrada anterior con Canvas vacío y con nodos MIND-002; downgrade/upgrade e integridad referencial se comprueban en base temporal.

### Frontend y regresión

- `node --check`, pruebas existentes, pytest y Ruff; smoke HTTP/API con `LIFEOS_DATA_DIR` temporal.
- Verificar operación por teclado y touch para cada capacidad; foco, nombres accesibles, anuncios, Escape, undo/redo y recuperación de error.
- Revisar visualmente 1440×900, 768×1024 y 390×844 en cada tema disponible; sin overflow horizontal ni controles esenciales inaccesibles.
- Regresión MIND-002: Spaces, Inbox, Cards, editar Note, drag individual, pan, zoom, teclado, archivado y persistencia.
- No incorporar frameworks ni dependencias runtime para las pruebas o el Canvas.

## 15. Criterios de aceptación

1. Una Note existente se añade de forma explícita a un Canvas conservando su ID, contenido y membresía en Inbox; no se duplica dentro del mismo Canvas.
2. Las conexiones visuales persisten entre dos Cards del mismo Canvas, no tienen semántica ni afectan los datos canónicos y desaparecen al quitar cualquiera de sus extremos.
3. El usuario puede seleccionar y mover varias Cards como una operación indivisible.
4. Resize y orden visual persisten y se restauran al reabrir el Canvas.
5. Cada operación espacial confirmada puede deshacerse y rehacerse después de una recarga, dentro del límite documentado; una operación inválida no deja estado parcial.
6. La eliminación de una Note no deja referencias/historial que puedan restaurarla; el efecto sobre historial se informa antes de confirmar.
7. Conexiones y representación espacial sobreviven export/import/backup/restore según sus contratos y pruebas temporales.
8. Las capacidades de MIND-002 siguen funcionando sin regresiones en tres viewports y temas disponibles.
9. Con teclado y touch se puede añadir, seleccionar, mover, conectar, redimensionar, ordenar, deshacer y rehacer sin depender de color, hover o drag como único método.
10. No hay frameworks, servicios remotos, contenido duplicado, código de Home ni cambios a Evolution.
11. MIND-003 permanece PLANNING hasta que Opus, Sonnet y el PO completen sus gates; esta SPEC no habilita código.

## 16. Supuestos y riesgos pendientes

- La revisión técnica sobre el tamaño y forma del historial, constraints compuestos y coordinación con el borrado canónico de Notes está pendiente de Sonnet.
- El flujo de conexión, lasso en touch, tamaño mínimo y utilidad de frames están pendientes de revisión UX de Opus. Frames quedan fuera mientras tanto.
- La estrategia de integración Alembic está pendiente de decisión del PO; MIND-003 no la resuelve.
- El worktree `product/mind-core` tiene cambios locales MIND-003A sin publicar. No son autoridad aprobada ni se incorporan automáticamente a esta SPEC; ver HANDOFF.
