# Inicio de trabajo para el agente de implementación

**Leer antes de ejecutar cualquier tarea.**

Fuente de alcance y estado: docs/factory/work/WORK_QUEUE.md. Toda tarea READY requiere leer su SPEC completa.

## 1. Rama de trabajo

La documentación de evolución se encuentra en la rama remota product/lifeos-evolution, creada desde main en el commit 27791fc8a157a8733f5bb322a7f19c845a251995.

Trabajar únicamente en esa rama, salvo asignación expresa del PO. No implementar directamente en main.

Antes de cambiar de rama:
1. ejecutar git status --short;
2. revisar y preservar cambios locales y archivos no trackeados;
3. ejecutar git fetch origin;
4. si el árbol está limpio y la rama local existe, cambiar a product/lifeos-evolution y actualizar con git pull --ff-only;
5. si el árbol está limpio y no existe, crearla siguiendo origin/product/lifeos-evolution.

Si hay cambios locales, conflictos o archivos desconocidos, no ejecutar stash, reset, clean, checkout destructivo ni sobrescritura automática. Detenerse y reportar.

**Precaución conocida de STAB-001:** el commit local `f99722d` y el archivo no trackeado `contexto_lifeos.txt` fueron reportados previamente y no se confirmó que el commit estuviera en el remoto. Antes de sincronizar, comparar explícitamente los hashes local/remoto y los commits ahead/behind. Preservar ambos elementos si siguen presentes. Si existe divergencia, no intentar push directo, rebase, merge ni force push; informar hashes y divergencia al PO para decidir cómo reconciliar. No perder el trabajo de QA.

## 2. Orden de lectura

1. AGENTS.md
2. VISION.md
3. ROADMAP.md
4. REQUIREMENTS.md
5. ARCHITECTURE.md
6. DATABASE.md
7. SECURITY.md
8. docs/product/
9. docs/factory/work/WORK_QUEUE.md
10. SPEC.md de la tarea.

## 3. Delegación y orden de trabajo vigente

WORK_QUEUE.md es la fuente de verdad para estado, prioridad, responsable y dependencias. No usar listas antiguas de asignaciones de Fase 9 como autorización vigente: las entregas anteriores figuran en REVIEW.

### Fase 9.1 — Interacción directa y experiencia fluida

Responsable de implementación: Mimo (Developer). Rama: product/lifeos-evolution.

Orden obligatorio:
1. RESPONSIVE-002 — corregir el overflow horizontal móvil conocido.
2. UX-HOME-002 — claridad, exactitud y captura rápida de Home.
3. UX-WIDGETS-002 — modo Personalizar en Home y reordenamiento drag & drop dentro de las zonas existentes.
4. UX-MODULES-002 — formularios progresivos de Projects/Notes y edición de notas.
5. UX-REVIEW-002 — revisión UX sin código por un agente distinto de Mimo (Copilot UX, si está disponible).

Las cuatro primeras tareas tienen SPEC y estado READY. Se ejecutan secuencialmente, una por una, respetando la dependencia y verificando el cierre técnico de cada entrega antes de comenzar la siguiente. UX-REVIEW-002 permanece PLANNING hasta que las implementaciones estén en REVIEW.

El PO aprobó el reordenamiento dentro de las zonas actuales. No está aprobado mover widgets entre zonas/columnas ni cambiar el modelo de datos. No iniciar esa extensión.

Las entregas previas STAB-001, BUG-001, HAB-002, PRJ-UI-001, HOME-001, TASK-001 y UX-REVIEW-001 permanecen en REVIEW hasta aceptación del PO; no reabrirlas salvo regresión o tarea específica.

PRJ-WORKSPACE-001, PRJ-PLAN-001 y ANALYTICS-001 siguen PLANNING: autorizan diseño/documentación solamente, nunca código ni migraciones.

## 4. Autonomía y límites

Autorizado:
- implementar tareas READY de Fase 9;
- corregir defectos directamente relacionados;
- agregar pruebas;
- actualizar documentación técnica afectada;
- crear commits locales de checkpoint después de verificar las pruebas;
- hacer push obligatorio de esos commits a la rama remota de trabajo asignada.

No autorizado:
- push a main;
- merge a main o a ramas ajenas;
- force push o reescritura destructiva de historia;
- migraciones, nuevos modelos o cambios de esquema;
- dependencias/frameworks o cambios de arquitectura;
- IA runtime, proveedores externos o integraciones;
- LAN, Internet, cloud, sync o multiusuario;
- modificar datos personales o secretos;
- borrar archivos no trackeados o cambios ajenos;
- cambiar visión, alcance, seguridad o requisitos por iniciativa propia.

El push a la rama de trabajo asignada es parte obligatoria del trabajo y no requiere autorización adicional. Merge, release y despliegue sí requieren autorización expresa del PO.

Ante un límite no autorizado, detener esa parte, documentar alternativas y continuar con tareas READY independientes.

## 5. Reglas de implementación

- Implementar cambios pequeños y verticales.
- No reescribir un módulo entero si basta un cambio localizado.
- Reutilizar API, tokens y componentes.
- Mantener IDs de widgets y preferencias.
- No inventar series históricas, health score o resultados.
- Formularios conservan los valores ante errores.
- El progreso de tareas no es progreso de resultados.
- Mantener estados de carga, vacío, error, éxito y confirmación.
- Mantener semántica, foco, teclado y responsive.

## 6. Verificación y publicación obligatoria

Según los archivos afectados:
- pytest -q desde backend;
- ruff check app tests desde backend;
- node --check para JS modificado;
- smoke test con LIFEOS_DATA_DIR temporal;
- revisión visual 1440×900, 768×1024 y 390×844;
- teclado, foco, consola y overflow.

Para cada tarea o checkpoint seguro:
1. revisar git diff y git status;
2. ejecutar las pruebas pertinentes y registrar sus resultados reales;
3. crear un commit descriptivo en la rama asignada;
4. ejecutar git push -u origin <rama> la primera vez, o git push origin <rama> en adelante;
5. verificar con git status y git rev-parse HEAD que el commit publicado es el esperado; si hace falta, comprobar también origin/<rama>;
6. no continuar como si estuviera publicado si el push falló.

No usar force push. Si el remoto avanzó o el push es rechazado, preservar el trabajo y reportar la divergencia para resolverla sin perder cambios ajenos.

Antes de entregar:
- listar archivos modificados;
- incluir comandos exactos y resultados reales;
- separar comprobado, supuesto y pendiente;
- declarar si la revisión fue independiente;
- informar rama, hash del commit y estado verificable del push.

## 7. Entrega

Al terminar:
1. actualizar WORK_QUEUE.md;
2. completar templates/handoff-template.md;
3. dejar en REVIEW, no DONE;
4. crear commit y hacer push a la rama asignada;
5. verificar que el remoto contiene el commit;
6. no hacer merge.

El Product Owner acepta la entrega y decide merge/publicación.

## 8. Si se agota el contexto

No comenzar otra tarea si no se puede terminar de forma segura la actual. Dejar un handoff preciso. Publicar un checkpoint seguro en la rama de trabajo para que el siguiente agente pueda continuar; si no es posible hacer push, explicar exactamente por qué. No afirmar que está terminada si faltan pruebas.