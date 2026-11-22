# MIND-002 — Primer núcleo funcional: Spaces, Inbox y Canvas con Cards simples

**Prioridad:** P0  
**Estado:** READY  
**Rol:** Developer — Mimo  
**Revisión:** Reviewer independiente cuando esté disponible  
**Rama de implementación:** `product/mind-core` (crear solo después de comprobar que no existe y de verificar el HEAD base)  
**Base:** HEAD remoto actual de `product/lifeos-evolution`, verificado al iniciar. No usar el SHA histórico del borrador MIND-001 como base sin comprobarlo.

## 1. Objetivo

Entregar la primera versión realmente utilizable de Mind: el usuario puede crear contextos de trabajo (Spaces), capturar ideas en una Inbox transversal, crear y abrir Canvases y colocar Cards de texto simples que conserven su contenido y posición después de cerrar y volver a abrir la aplicación.

Mind funciona sin IA, sin conexión a Internet y sin proveedores externos.

## 2. Alcance funcional

### 2.1 Navegación y entrada a Mind
- Incorporar Mind a la navegación existente sin rehacer el shell completo.
- Ruta principal de Mind con listado de Spaces y acceso persistente al Inbox.
- Estados de carga, vacío, error y reintento.
- Mantener intactas las rutas y módulos existentes.

### 2.2 Spaces
- Crear Space con nombre obligatorio y descripción opcional.
- Listar y abrir Spaces.
- Renombrar y editar descripción.
- Archivar y restaurar.
- No convertir Spaces en una jerarquía de carpetas rígida.
- Un Space archivado no debe perder sus Canvases ni contenido.
- Definir eliminación física solo si se demuestra segura y no destructiva; preferir archivado.

### 2.3 Inbox transversal
- Debe existir un único Inbox reservado para toda la instalación, no uno por Space.
- No se puede renombrar, archivar ni eliminar desde la UI.
- El servicio debe garantizar su creación idempotente y recuperación si falta.
- La BD debe impedir más de un Inbox (por ejemplo, índice único parcial en `is_inbox`); la garantía de existencia se implementa en bootstrap/servicio transaccional.
- Captura rápida: texto/contenido obligatorio, título opcional; guardar crea una Note canónica y su membresía en Inbox.
- La captura se puede consultar y editar desde Inbox usando el servicio/API canónico de Notes.
- Clasificar/mover una captura debe ser una acción explícita. Añadir una representación en Canvas no debe borrar el contenido ni eliminar membresías inadvertidamente.
- Errores de guardado preservan el borrador.

### 2.4 Canvases
- Crear Canvas dentro de un Space, listar, abrir, renombrar, editar descripción, archivar y restaurar.
- Canvas tiene identidad y metadatos propios.
- Al abrir, muestra el área de trabajo con un estado vacío útil y la acción para crear la primera Card.
- No implementar todavía conexiones semánticas, grupos avanzados ni motor de documentos ricos.

### 2.5 Cards simples de texto
- Permitir crear una Card de texto/idea desde el Canvas.
- La Card tiene título y cuerpo de texto simple.
- Crear/editar contenido debe usar una única fuente de verdad; en esta entrega se puede reutilizar Notes existente si la auditoría confirma que cubre los requisitos sin duplicar el modelo.
- La instancia visual se guarda por separado del contenido canónico: Canvas, posición, tamaño inicial y orden visual.
- Permitir mover la Card y guardar su posición en backend al terminar la interacción; mostrar estado de guardado/ error.
- Una recarga debe restaurar Cards y posiciones.
- Quitar una Card del Canvas no elimina la Note.
- Borrar una Note canónica requiere confirmación y elimina referencias visuales inválidas de forma consistente.

### 2.6 Interacción espacial mínima
- Canvas con pan y zoom básicos, con controles visibles y alternativa por teclado.
- Drag de Card sin arrastrar accidentalmente al seleccionar texto o activar controles internos.
- No persistir cada frame de movimiento; guardar en drag end/debounce y gestionar fallos.
- Coordenadas del mundo independientes del viewport y del zoom. El modelo debe permitir abrir el mismo Canvas con distintas dimensiones de pantalla conservando la ubicación relativa de las Cards.
- En móvil, si drag/pan/zoom compiten con el scroll de página, definir una interacción táctil explícita y conservar un modo alternativo accesible.
- Las conexiones entre Cards quedan para MIND-003.

## 3. Modelo de datos y límites

Antes de migrar, inspeccionar el modelo real de Notes, Projects, Tasks, Hábitos, dashboard, eventos y exportación.

Tablas mínimas candidatas de esta entrega:
- `mind_spaces`
- `mind_canvases`
- `mind_space_notes`
- `mind_canvas_nodes`

No crear todavía `mind_canvas_edges`, `mind_content_relations`, tablas de documentos por bloques, sesiones de Orbe, artefactos ni tablas preparatorias para etapas futuras.

Reglas:
- UUIDv4 texto y timestamps UTC según convenciones existentes.
- FK explícitas donde corresponda; validar referencias polimórficas en servicio y pruebas si se adopta ese diseño.
- Un mismo contenido debe poder referenciarse sin duplicarse; el esquema no debe imponer una restricción que impida representarlo en más de un Canvas.
- Quitar nodo ≠ borrar contenido.
- Archivar Space/Canvas no elimina contenido canónico.
- Política de notas coherente con `REQUIREMENTS.md`: borrar Note elimina sus vínculos y referencias Mind; eliminar/mover Space nunca borra Notes.
- No cambiar la tabla Notes ni su API salvo que sea indispensable y se justifique en el handoff.

### Decisión técnica obligatoria antes de escribir código

Comparar el esquema del primer borrador con la base real y documentar brevemente:
1. cómo se crea y garantiza el Inbox único;
2. cómo se representa una Card de texto sin duplicar Notes;
3. cómo se conservan las referencias si una Note se elimina;
4. cómo se exportan y restauran los datos Mind;
5. qué queda expresamente para MIND-003 y MIND-004.

Si una migración afecta datos existentes, detenerse y elevar alternativas al PO antes de ejecutarla. No modificar la base personal para pruebas.

## 4. Exportación, backup y restauración

- Incluir Spaces, Canvases, membresías y nodos simples en el JSON versionado de exportación.
- SQLite backup debe cubrir las tablas nuevas.
- Agregar pruebas de exportación/restore con base temporal, preservando IDs y referencias.
- No afirmar que exportación/restauración funciona sin ejecutar pruebas de ida y vuelta.

## 5. UX y accesibilidad

- Mantener dirección visual de LifeOS y patrones existentes.
- Canvas libre, no una lista de tarjetas disfrazada.
- Captura rápida accesible desde las vistas de Mind; evaluar un acceso global común solo si no exige rehacer el shell.
- Evitar formularios gigantes y acciones permanentes en cada tarjeta.
- Edición de título/cuerpo sencilla; guardar/cancelar claro.
- Teclado: foco visible, acceso a creación/edición, movimiento alternativo al drag, Escape cancela interacción sin guardar cambios incompletos.
- Móvil/tablet: sin overflow horizontal; acciones táctiles utilizables.
- Estados de carga/vacío/error/éxito; mensajes de guardado comprensibles.
- Viewports mínimos: 1440×900, 768×1024 y 390×844, en temas disponibles.

## 6. Fuera de alcance

- Orbes, chat, IA, voz, proveedores o llamadas remotas.
- Documentos por bloques, editor enriquecido, tablas/formularios complejos.
- Video/audio/embeds externos e importación de archivos.
- Relaciones semánticas y motor de conexiones entre Cards.
- Mind maps automáticos.
- Colaboración, sincronización cloud o multiusuario.
- Frameworks frontend, bundlers o librerías de Canvas sin aprobación.

## 7. Criterios de aceptación

1. La aplicación ofrece entrada Mind y las rutas existentes siguen funcionando.
2. Se crea, lista, renombra y archiva un Space.
3. Existe exactamente un Inbox por instalación tras el bootstrap; no puede crearse un segundo ni eliminarse desde UI.
4. Capturar una idea crea una Note canónica y aparece en Inbox.
5. La captura se conserva al reiniciar la aplicación.
6. Se crea, abre, renombra y archiva un Canvas dentro de un Space.
7. Se crea una Card de texto/idea y se puede editar.
8. Se mueve una Card y la posición persiste después de cerrar/abrir el Canvas.
9. Quitar una Card no elimina su Note.
10. Eliminar una Note con confirmación no deja referencias Mind huérfanas.
11. Export JSON incluye los datos Mind; backup/restore SQLite se verifica con DB temporal.
12. No se introducen dependencias runtime ni se necesita Internet/IA.
13. pytest, Ruff y node --check pasan; QA visual en los tres viewports sin hallazgos críticos.
14. Se revisa el diff completo y la entrega queda en REVIEW, no DONE.

## 8. Dependencias y archivos

El Developer debe inspeccionar antes de editar:
- navegación/router y patrones de vistas frontend;
- Notes: modelos, schemas, repository, service, API y UI;
- dashboard/home y captura rápida actual;
- base/configuración y Alembic;
- export/backup/restore;
- activity_events;
- tests y fixtures temporales.

No asumir rutas exactas ni copiar estructuras sin verificar el código actual.

## 9. Proceso de trabajo

1. Verificar Git status, rama y worktrees. No tocar ni cambiar de rama en el worktree de Evolution.
2. Actualizar refs remotas y verificar el HEAD actual de `product/lifeos-evolution`.
3. Crear worktree separado `LifeOS-mind-implementation` y rama `product/mind-core` desde ese HEAD. Si la rama o el path ya existen, detenerse y reportarlo; no sobrescribir.
4. Traer solo los documentos Mind aprobados desde `planning/mind-001`; no fusionar la rama de planificación completa.
5. Implementar por porciones pequeñas; mantener este SPEC y el roadmap como alcance.
6. Probar con base temporal y revisar diff.
7. Commit y push únicamente a `product/mind-core`; nunca a main ni a Evolution.
8. Informar hash, archivos, pruebas reales, QA visual, riesgos y pendientes. Estado REVIEW.

Ante modificaciones ajenas, worktree sucio, conflictos o divergencia inesperada: preservar y detenerse. No reset, clean, stash destructivo, rebase destructivo ni force push.
