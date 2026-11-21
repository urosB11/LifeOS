# HAB-002 — Semana interactiva y calendarios por hábito

**Prioridad:** P1 · **Responsable:** Developer — Mimo (asignación explícita del PO) · **Reviewer independiente:** Nemo · **Estado:** READY

## Objetivo

Mejorar el seguimiento visual y la edición de hábitos desde Home y Habit Tracker. La semana de Home debe funcionar como checklist; Habit Tracker debe mostrar los calendarios mensuales de todos los hábitos en una vista conjunta, sin selector de un único hábito.

## 1. Home — Semana de hábitos

### Presentación
- Eliminar el scroll horizontal del widget. Los siete días deben entrar en el ancho disponible.
- Reemplazar la tabla que fuerza overflow por una matriz compacta y responsive: nombre del hábito + siete días.
- En pantallas angostas reducir espacios y dimensiones de celdas; no esconder días ni crear un segundo scroll horizontal.
- Mantener alineación de las fechas por columna entre hábitos.
- Un día no programado mantiene el espacio de alineación, pero no muestra casillero, borde, fondo, símbolo ni color.

### Estados visuales
Los estados visuales se derivan de programación, fecha local y registro. No agregar estados persistidos nuevos.

| Condición | Etiqueta | Tratamiento |
|---|---|---|
| Programado y cumplido | Cumplido | Verde |
| Registro cuantificable inferior a la meta | Parcial | Azul/info suave |
| Programado, hoy, sin registro | Pendiente de registrar | Amarillo muy apagado / espera |
| Programado, fecha pasada, sin registro | No cumplido | Rojo suave |
| Registro marcado voluntariamente como omitido | Omitido | Amarillo apagado, distinguible con raya/ícono |
| Programado, fecha futura | En espera | Gris |
| No programado | Ninguna | Vacío, sin casillero visible |

- La fecha se interpreta en la zona horaria local configurada por LifeOS.
- "No cumplido" es un estado derivado para una fecha programada anterior a hoy que no tiene registro. No se guarda como un nuevo status en la base.
- Mantener los valores persistidos actuales: `completed`, `pending` y `skipped`. En UI, `pending` significa registro parcial/sin completar, no ausencia de registro.
- La leyenda debe coincidir exactamente con los estados visibles. No llamar "pendiente de registrar" a un registro parcial.

### Interacción / checklist
- Las fechas programadas de hoy o anteriores son editables desde Home.
- Clic en una celda abre una edición compacta accesible por teclado:
  - Hábito binario: marcar cumplido, marcar omitido o quitar el registro.
  - Hábito cuantificable: mostrar valor actual, permitir ingresar/corregir cantidad y guardar; el backend determina cumplido/parcial según la meta configurada.
  - Permitir corregir un registro anterior, incluido un día que aparece como "No cumplido".
- Una fecha futura aparece gris y deshabilitada: no debe permitir registrar.
- Los días no programados no tienen interacción.
- Tras guardar/corregir/eliminar, refrescar la semana y cualquier resumen afectado sin recargar toda la aplicación.
- Mostrar errores sin perder el contexto de edición y evitar doble envío.

## 2. Habit Tracker — Calendarios de todos los hábitos

- Eliminar el selector `#cal-habit` de un único hábito.
- Mostrar un calendario mensual por cada hábito no archivado (activos y pausados), con su nombre y color.
- Disponer las tarjetas en una grilla visual horizontal de varias columnas en escritorio; reorganizar en tablet/móvil sin overflow horizontal global.
- Todos los calendarios comparten el mismo mes y año. Un único control anterior/siguiente cambia todos a la vez.
- Mantener una sola leyenda general.
- Mantener grilla mensual de lunes a domingo y resaltar hoy de forma accesible.
- Reutilizar exactamente la semántica de estados definida en Home.
- Las fechas programadas de hoy o anteriores también se pueden abrir para corregir/registrar; fechas futuras se ven grises y no son editables; días no programados quedan vacíos.
- No convertir la vista en un carrusel con scroll horizontal permanente. Priorizar una grilla legible y responsive.

## 3. API y datos

Reutilizar endpoints existentes:
- `GET /api/v1/habits/week`
- `POST /api/v1/habits/{id}/entries`
- `PATCH /api/v1/habits/{id}/entries/{entry_date}`
- `DELETE /api/v1/habits/{id}/entries/{entry_date}`
- `GET /api/v1/habits/{id}/calendar?month=YYYY-MM`

Si la UI necesita el valor cuantitativo actual para editar desde semana/calendario, extender las respuestas de semana y calendario con un campo opcional como `entry_value`. No crear una ruta nueva si los contratos existentes alcanzan.

Reglas ya existentes que deben preservarse:
- POST permite crear registros de fechas anteriores si están programadas.
- PATCH corrige un registro ya existente.
- DELETE elimina el registro y devuelve el día a no registrado.
- Los días futuros y no programados son rechazados por backend.
- El estado de un registro cuantificable se deriva al guardar la cantidad en relación con la meta.

## 4. Métricas y persistencia

- No agregar `missed` ni `future` a `habit_entries.status`.
- No crear migración de base de datos para estados puramente derivados.
- Mantener días programados pasados sin completar dentro del denominador de cumplimiento; no contarlos como completados.
- Mantener la distinción de métricas documentada: cumplimiento cuenta `completed`; consistencia cuenta `completed + skipped`.
- No recalcular silenciosamente registros históricos al cambiar la frecuencia.

## No incluir

- Rediseño completo del módulo de hábitos.
- Nuevas métricas, rachas o gamificación.
- Motor de recurrencias, notificaciones o recordatorios.
- Cambios de arquitectura, frameworks o dependencias.

## Criterios de aceptación

1. Semana de Home muestra los siete días sin scroll horizontal a 1440×900, 768×1024 y 390×844.
2. La matriz es usable con teclado y tiene etiquetas accesibles por fecha y hábito.
3. Los siete estados de la tabla se distinguen según la semántica especificada; no programado es realmente vacío.
4. Un día pasado sin registro se muestra "No cumplido" y puede registrarse desde Home.
5. Se puede crear, modificar y quitar un registro anterior desde Home, con y sin objetivo cuantificable.
6. Una fecha futura no permite interacción ni escritura.
7. Habit Tracker muestra un calendario por cada hábito activo/pausado, todos sincronizados en el mes.
8. Cambiar mes actualiza todos los calendarios.
9. La vista no introduce overflow horizontal de página en desktop, tablet o móvil.
10. Se conservan modo claro/oscuro, estados de carga/vacío/error y la información existente.

## Pruebas requeridas

- Tests de servicio/API para valores de semana/calendario y cambios de registros históricos.
- Tests de fechas programadas y no programadas, pasado/hoy/futuro, hábitos binarios y cuantificables.
- Verificar cumplimiento/consistencia sin nuevos estados persistidos.
- `node --check`, `pytest -q`, `ruff check app tests` y smoke con `LIFEOS_DATA_DIR` temporal.
- QA visual 1440×900, 768×1024, 390×844; teclado, foco, consola y overflow.
- No usar ni modificar la base personal.

## Entrega

Actualizar handoff y WORK_QUEUE, revisar el diff, crear commit descriptivo y hacer push obligatorio a `origin/product/lifeos-evolution`. Verificar que el commit está en remoto. No hacer merge ni push a main. Dejar en REVIEW; Nemo realiza revisión independiente.