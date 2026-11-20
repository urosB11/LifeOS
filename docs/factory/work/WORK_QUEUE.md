# WORK_QUEUE — Cola central de trabajo

**Propósito:** Registro central de tareas, responsables, estados y dependencias.
**Mantenimiento:** Coordinator actualiza; Product Owner prioriza.

## Estados posibles

| Estado | Significado |
|--------|-------------|
| `BACKLOG` | Creada, no asignada |
| `PLANNING` | En planificación |
| `IN_PROGRESS` | En implementación |
| `REVIEW` | En revisión |
| `APPROVED` | Aprobada por PO, pendiente de cierre |
| `DONE` | Completada y cerrada |
| `BLOCKED` | Bloqueada por dependencia o decisión |
| `CANCELLED` | Cancelada por PO |

## Formato de entrada

```
### [ID]: [Título]
- **Estado:** [BACKLOG / PLANNING / IN_PROGRESS / REVIEW / APPROVED / DONE / BLOCKED / CANCELLED]
- **Prioridad:** P0 / P1 / P2
- **Rol responsable:** [Developer / Reviewer / UX Designer / Auditor / Coordinator]
- **Asignado a:** [nombre del agente, ej. Nemo, Claude, Mimo]
- **Dependencias:** [IDs de tareas dependientes o "ninguna"]
- **Fecha creada:** YYYY-MM-DD
- **Notas:** [contexto relevante]
```

---

## Tareas activas

### UX-001: Auditoría UX de Home, Habits, Projects y Tasks
- **Estado:** DONE
- **Prioridad:** P0
- **Rol responsable:** UX Designer
- **Asignado a:** Claude
- **Dependencias:** ninguna
- **Fecha creada:** 2026-11-20
- **Notas:** Auditoría completada. Informe presentado con 3 alternativas de rediseño. Pendiente: aprobación de PO para implementar backlog.

### FACTORY-001: Crear estructura docs/factory/
- **Estado:** DONE
- **Prioridad:** P1
- **Rol responsable:** Developer
- **Asignado a:** Nemo
- **Dependencias:** ninguna
- **Fecha creada:** 2026-11-20
- **Notas:** Estructura creada con roles, flujos, plantillas, decisiones y cola de trabajo.

---

## Tareas pendientes (sin asignar)

### UX-002: Implementar backlog P0 de auditoría UX
- **Estado:** BACKLOG
- **Prioridad:** P0
- **Rol responsable:** Developer + UX Designer
- **Asignado a:** (sin asignar)
- **Dependencias:** UX-001
- **Fecha creada:** 2026-11-20
- **Notas:** Requiere aprobación de PO. Incluye: Home jerárquico, racha en calendario, salud de proyectos, búsqueda global, separación de Settings.

### FASE-9: Siguiente fase del roadmap
- **Estado:** BACKLOG
- **Prioridad:** P1
- **Rol responsable:** (sin definir)
- **Asignado a:** (sin asignar)
- **Dependencias:** UX-002 (recomendado)
- **Fecha creada:** 2026-11-20
- **Notas:** Pendiente de definición por PO. No iniciar sin autorización.

---

*(Agregar nuevas entradas debajo de esta línea)*
