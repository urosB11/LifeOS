# UX-HOME-002 — Claridad, exactitud y captura contextual en Home

**Prioridad:** P1 · **Responsable:** Developer — Mimo · **Estado:** READY  
**Dependencia:** RESPONSIVE-002 · **Rama:** product/lifeos-evolution.

## Problema

HOME-001 consolidó Home como centro diario, pero quedan fricciones funcionales:
- Las tareas vencidas y las que vencen hoy aparecen en Atención y nuevamente en Hoy.
- Si la consulta de tareas falla, el encabezado puede interpretar null como lista vacía y decir que no hay pendientes.
- Los proyectos sin tareas pueden mostrarse como 0/0 y una barra 0 %, aunque el contrato de producto exige “Sin tareas”.
- Captura rápida presenta simultáneamente dos formularios; el de Nota solo solicita título, sin espacio explícito para escribir contenido.

## Objetivo

Hacer que Home comunique el estado real sin duplicar elementos y permita capturar tareas/notas con menos fricción, manteniendo su papel de centro de operaciones.

## Diseño funcional requerido

### 1. Atención y Hoy sin duplicados

- Atención contiene exclusivamente tareas pendientes vencidas y con vencimiento hoy.
- Hoy muestra tareas pendientes relevantes que NO aparecen en Atención.
- Las colecciones deben ser disjuntas por ID.
- Mantener el orden actual de relevancia para Hoy: próximas fechas, prioridad alta y tareas sin fecha según las reglas existentes; revisar el orden para que una tarea no aparezca dos veces.
- Mantener límites visuales actuales y enlaces al módulo completo; el contador “más” debe referirse al conjunto correcto.
- Si Atención está vacía, mostrar el estado tranquilo actual.
- Si Hoy está vacío pero la consulta fue exitosa, mostrar un vacío honesto y útil.

### 2. Estado de datos honesto

- Diferenciar lista vacía (consulta exitosa sin resultados) de consulta fallida (data null/error).
- Si las tareas no pudieron cargarse, el encabezado no puede afirmar “No hay tareas pendientes” ni mostrar un conteo cero como si fuera real.
- Mostrar un mensaje contextual breve y un acceso de reintento cuando sea apropiado.
- Un error de tareas no debe borrar los bloques de proyectos o hábitos que sí cargaron.
- Nunca reemplazar error por estado vacío.

### 3. Proyectos sin tareas

- Si task_count es cero, mostrar “Sin tareas”.
- No mostrar una barra de progreso ni 0 % con denominador cero.
- Para proyectos con tareas, conservar la métrica “Ejecución de tareas” y su semántica exacta.
- No introducir “salud”, porcentaje de resultado ni indicadores sintéticos.

### 4. Captura rápida unificada

- Mantener una única superficie de Captura rápida.
- Mostrar un selector accesible de modo Tarea / Nota; solo un editor activo a la vez.
- Si uno de los dos widgets está oculto por preferencia, no mostrar una opción deshabilitada ni vacía para ese modo.
- Conservar los IDs quick_add_task y quick_add_note, así como su visibilidad independiente.
- Tarea: título obligatorio; proyecto opcional si existen proyectos. No exigir fecha ni prioridad.
- Nota: título obligatorio y un campo de contenido de texto disponible; el contenido puede ser opcional/vacío según el contrato actual, pero debe ser posible escribirlo desde Home.
- Usar POST /tasks y POST /notes actuales. No agregar endpoints ni cambiar esquema.
- No mostrar los dos formularios a la vez.
- Al cambiar de modo, no enviar ni borrar silenciosamente el borrador del otro modo.
- Tras guardar, actualizar los bloques afectados; evitar doble envío.
- Ante error HTTP/red/validación, conservar el borrador y mostrar el error junto al editor.

### 5. Zona horaria

- Las fechas de Home deben respetar la zona horaria configurada en Settings, no depender accidentalmente de la zona horaria del sistema operativo.
- Reutilizar GET /settings/timezone y APIs nativas Intl si alcanzan.
- No cambiar la fecha de vencimiento almacenada ni introducir conversiones UTC para fechas calendario.
- Si no es posible respetar la zona configurada con el contrato actual, documentar la limitación y detener solo esa parte; no crear un endpoint sin aprobación.

## Compatibilidad y dirección visual

- Conservar la dirección calma/editorial, jerarquía Atención → Hoy → Proyectos → Hábitos → Captura.
- No volver a seis tarjetas KPI iguales.
- Mantener widgets existentes, IDs, orden y visibilidad.
- Mantener tema claro/oscuro.
- Evitar tarjetas anidadas o controles persistentes innecesarios.
- Reutilizar componentes/tokens ya existentes.
- No reescribir todo home.js si los cambios pueden ser localizados.

## No incluir

Drag & drop y cambio de orden (UX-WIDGETS-002); movilidad entre zonas; gráficos históricos; objetivos/hitos; IA; métricas nuevas; cambios de API/modelo; librerías o migraciones.

## Criterios de aceptación

1. Ninguna tarea aparece simultáneamente en Atención y Hoy.
2. Atención y Hoy mantienen sus límites, orden y enlaces.
3. Fallo de consulta no se presenta como cero o vacío.
4. Proyecto sin tareas muestra “Sin tareas”, sin barra 0 %.
5. Captura ofrece modo Tarea/Nota y un editor visible a la vez.
6. Nota se puede crear con título y contenido desde Home.
7. Los borradores sobreviven al error y al cambio de modo.
8. Fecha local coherente con timezone configurado.
9. Widgets y preferencias existentes siguen funcionando.
10. Accesibilidad, teclado, responsive y ambos temas sin regresiones.

## Pruebas

Fixtures con tareas vencidas, de hoy, futuras, alta prioridad, sin fecha y completadas. Asegurar partición disjunta. Probar consulta fallida vs lista vacía; proyecto sin tareas y proyecto con tareas; captura tarea/nota, modos, ocultar cada widget, POST fallido, doble click, Enter/Escape, timezone distinto del sistema. pytest, Ruff, node --check, smoke temporal, diff y QA visual.

## Entrega

Actualizar handoff y cola; informar archivos, reglas de clasificación, pruebas reales y capturas. Commit y push a product/lifeos-evolution. Estado REVIEW, no DONE.
