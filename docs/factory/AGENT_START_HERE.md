# Inicio de trabajo para el agente de implementación

**Leer antes de ejecutar cualquier tarea.**

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

## 3. Delegación autónoma vigente

El Product Owner autorizó ejecutar autónomamente las tareas READY de Fase 9 que tengan especificación. No solicitar confirmación para decisiones rutinarias dentro de esos límites.

Orden de trabajo y responsabilidades:
1. STAB-001 — Mimo completa la revisión independiente de Fase 8. Solo revisión, sin código.
2. BUG-001 — Nemo corrige la pérdida de estado del formulario ante error.
3. HAB-002 — Mimo toma temporalmente el rol Developer asignado por el PO; Nemo hace la revisión independiente. Implementa semana interactiva y calendarios por hábito.
4. PRJ-UI-001 — Mimo como Developer; Nemo como Reviewer. Mantiene la lista de tareas visible al abrir el formulario del proyecto. Esperar a BUG-001 para no solapar cambios en projects.js.
5. HOME-001 — Nemo; esperar HAB-002 por solapamiento en home.js.
6. TASK-001 — Nemo, después de HOME-001.
7. UX-REVIEW-001 — Mimo realiza la revisión independiente después de HOME-001 y TASK-001.

La asignación de rol es por tarea. Mimo primero debe completar STAB-001 como Reviewer; luego puede asumir Developer únicamente en HAB-002 y PRJ-UI-001. No debe revisar su propia implementación: Nemo es el Reviewer de esas dos entregas.

PRJ-WORKSPACE-001, PRJ-PLAN-001 y ANALYTICS-001 siguen siendo PLANNING: autorizan diseño/documentación solamente, nunca código ni migraciones.

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