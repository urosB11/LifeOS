# STAB-001 — Validación manual de Fase 8

**Prioridad:** P0 · **Responsable:** Reviewer — Mimo · **Estado:** READY  
**Tipo:** revisión manual; no implementar cambios.

## Objetivo

Comprobar comportamiento visual y funcional en main después de Fase 8, PRJ-001, PRJ-002 y HAB-001.

## Pantallas

Home; Proyectos (listado y detalle); creación de tarea desde proyecto; Tareas; Hábitos; Notas; Settings.

## Matriz mínima

| Viewport | Tamaño |
|---|---|
| Desktop | 1440 × 900 |
| Tablet | 768 × 1024 |
| Móvil | 390 × 844 |

## Flujos

- abrir proyecto, crear tarea, cancelar y reabrir formulario;
- crear tarea válida y comprobar métricas;
- probar error de API y comprobar conservación de campos;
- completar/reabrir tarea;
- probar proyecto sin tareas;
- navegar listado/detalle en móvil;
- navegar calendario de hábitos, cambiar hábito/mes y revisar tamaño;
- abrir/cerrar modales y comprobar foco;
- navegar por teclado;
- comprobar overflow horizontal, consola, vacíos y errores.

## Entrega

Informe con viewport, navegador, pasos reproducibles, severidad, capturas si es posible, comprobado/no reproducido/pendiente. No modificar código ni marcar DONE.

Si no hay acceso al navegador local, indicarlo; no afirmar que hubo validación visual.