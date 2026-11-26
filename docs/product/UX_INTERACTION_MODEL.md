# Modelo de interacción — LifeOS

**Versión:** 0.1 · **Fecha:** 22 de noviembre de 2026  
**Estado:** dirección aprobada para la Fase 9.1. Los límites de cada entrega están en su SPEC.

## 1. Propósito

LifeOS debe sentirse como un espacio de trabajo personal y un centro de operaciones, no como una colección de pantallas CRUD ni como un panel administrativo. La interacción acompaña el ciclo:

**Intención → planificación → ejecución → evidencia → aprendizaje → ajuste.**

La interfaz debe ayudar a decidir qué hacer, actuar sobre el objeto correcto, conservar el contexto y entender qué ocurrió. La reducción de botones o inputs es un medio, no el objetivo: nunca se elimina una acción importante solo para que la pantalla parezca más limpia.

## 2. Principios

1. Contexto antes que navegación: las acciones frecuentes se ejecutan donde aparece el objeto.
2. Jerarquía antes que decoración: atención y decisiones primero; métricas solo cuando aportan una lectura válida.
3. Revelado progresivo: mostrar el mínimo necesario y desplegar opciones secundarias cuando se solicitan.
4. Una fuente de verdad: Home resume; Projects, Tasks, Habits y Notes mantienen los datos canónicos.
5. Estado honesto: loading, empty, error, success y pending son estados diferentes.
6. Resiliencia: no perder borradores por errores, re-renderizados o cancelaciones involuntarias.
7. Consistencia: mismos significados de Guardar, Cancelar, Editar, Eliminar y confirmación en todos los módulos.
8. Control humano: no ejecutar ni descartar cambios importantes sin acción explícita del usuario.
9. Accesibilidad equivalente: teclado, botones alternativos, foco visible y targets táctiles adecuados.
10. Movimiento funcional: animar para mostrar una transición, no para decorar.

## 3. Patrones de interacción

| Tipo de intención | Comportamiento |
|---|---|
| Acción frecuente y reversible | Acción visible en la fila/tarjeta; feedback inmediato y estado actualizado. |
| Cambio breve de un dato | Edición inline, con Guardar/Cancelar explícitos. Enter confirma; Escape cancela. No guardar silenciosamente por blur. |
| Creación o edición de varios campos | Panel progresivo o editor dedicado, cerrado por defecto cuando no se está usando. La lista/contexto permanece visible. |
| Acción secundaria infrecuente | Menú contextual etiquetado, accesible con teclado y táctil. No ocultar la acción primaria. |
| Acción destructiva | Separada visualmente, confirmación explícita y explicación del efecto. |
| Error de validación o red | Mensaje próximo al campo/objeto; conservar el borrador y permitir reintentar. |
| Consulta fallida | Estado de error distinto del estado vacío; nunca mostrar cero o “sin datos” cuando no se pudo consultar. |
| Reordenamiento | Modo Personalizar, asa explícita, vista previa, Guardar/Cancelar, alternativa por teclado y anuncio accesible. |

## 4. Home

Home presenta una síntesis útil del día: atención urgente, acciones restantes relevantes, proyectos en marcha, hábitos programados y captura rápida. No crea copias ni métricas independientes.

- Una tarea se presenta una sola vez en el conjunto Atención/Hoy.
- Atención contiene vencidas y con vencimiento hoy.
- Hoy presenta las restantes relevantes sin repetir Atención.
- Una consulta fallida no se interpreta como ausencia de tareas.
- Un proyecto sin tareas muestra “Sin tareas”; no 0 %.
- La Captura rápida ofrece un único espacio con modos Tarea y Nota. Solo un editor aparece activo a la vez.
- La captura de nota permite título y contenido; los campos opcionales no deben bloquear el registro.
- Los hábitos conservan su estado registrado y las acciones directas de marcar/deshacer.
- Las métricas reflejan datos actuales y nunca se rotulan como resultado o salud si solo miden ejecución de tareas.

## 5. Personalización de widgets

UX-WIDGETS-003 amplía con autorización del PO la primera entrega, reemplazando las zonas fijas de Home por un grid responsive global. El orden guardado determina la colocación auto-flow; cada tarjeta tiene spans de columna/fila limitados y el contenido puede ampliar la altura si lo necesita.

El usuario activa Personalizar desde Home. En ese modo aparecen asas de arrastre y herramientas de visibilidad; en modo normal no se muestran controles permanentes.

- Arrastrar solo desde el asa, no desde toda la tarjeta.
- Mostrar un placeholder claro mientras se mueve.
- Permitir Guardar o Cancelar; guardar realiza una sola escritura final.
- Un error conserva el borrador y permite reintentar.
- Ofrecer mover arriba/abajo como alternativa de teclado y táctil.
- Conservar foco y anunciar nombre/posición después de mover.
- Redimensionar con un asa dedicada y una alternativa de teclado; anunciar el tamaño lógico resultante.
- Mostrar el destino de arrastre y el tamaño provisional sin permitir solapamientos.
- Ajustar los spans al ancho disponible en tablet y móvil sin sobrescribir las preferencias guardadas.
- Respetar prefers-reduced-motion.
- Captura rápida se mueve como grupo visual, pero quick_add_task y quick_add_note conservan visibilidad independiente.
- Limitar la captura de puntero/touch a las asas para no interferir con controles internos ni el scroll de la página.
- Guardar orden y tamaño juntos; Cancelar descarta ambos y un error de guardado conserva el borrador.
- Settings no ofrece un segundo editor de orden.

## 6. Formularios progresivos

- Projects: el alta comienza cerrada; la lista permanece visible al crear/cancelar/guardar.
- Notes: el alta comienza cerrada; incluye título y contenido; la lista y filtros permanecen visibles.
- Notes: abrir una nota permite editar título y contenido con el PATCH existente; conservar relaciones y etiquetas no modificadas.
- Tags: el alta puede comenzar cerrada, sin ocultar la lista ni el filtro.
- Tasks ya cuenta con panel compacto, edición y preservación de borrador: reutilizar sus convenciones, no rehacerlo.
- Habits mantiene accesible la acción de registrar y deshacer.

## 7. Accesibilidad y responsive

- HTML semántico y controles nativos.
- Toda acción disponible por mouse debe tener alternativa de teclado.
- No depender de hover, color o movimiento.
- Focus visible; al cerrar panel/modal, devolver foco al disparador.
- Los cambios de orden se anuncian con aria-live o mecanismo equivalente.
- Targets táctiles de al menos 44 × 44 CSS px cuando corresponda.
- Drag táctil solo desde el asa; el resto de la tarjeta conserva el scroll normal.
- Respetar prefers-reduced-motion.
- Validar escritorio 1440×900, tablet 768×1024 y móvil 390×844 en temas oscuro y claro.
- No corregir overflow ocultando contenido.

## 8. Restricciones de arquitectura y datos

Frontend HTML/CSS/JavaScript nativo; backend FastAPI; SQLAlchemy síncrono; SQLite; Alembic; API /api/v1. Reutilizar servicios, endpoints, IDs y componentes existentes.

No agregar frameworks, dependencias, endpoints, modelos ni migraciones en la Fase 9.1. No utilizar config_json para almacenar zona de widgets. No cambiar el dominio de Project/Task/Habit/Note. Tests con base temporal mediante LIFEOS_DATA_DIR. Notas y contenido de usuario se presentan como texto, no HTML ejecutable.

## 9. Semántica de métricas

Actividad, ejecución, entregables y resultados son conceptos distintos. Una barra de tareas completadas representa ejecución de tareas, no porcentaje de resultado ni salud del proyecto. Si no hay denominador, mostrar “Sin tareas”/“Sin datos”. No inventar velocidad, score, predicción o serie histórica.

## 10. Criterio de calidad

Una mejora de UX se considera útil si reduce pasos sin ocultar funciones, mantiene el contexto, comunica estados con honestidad, conserva datos ante fallos y puede completarse con mouse, teclado o táctil. La revisión visual debe probar flujos reales, no limitarse a que la pantalla compile.
