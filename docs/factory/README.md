# Life OS — Factory (Coordinación de trabajo)

**Estado:** estructura operativa
**Versión:** 0.1
**Fecha:** 20 de noviembre de 2026

> Este directorio organiza cómo se planifica, ejecuta, revisa y documenta el trabajo en Life OS. No reemplaza `AGENTS.md` ni los documentos de producto; los complementa con procedimientos de coordinación.

## Propósito

- Definir roles claros y responsabilidades.
- Estandarizar flujos de trabajo para features, bugs y releases.
- Proporcionar plantillas reutilizables para informes, handoffs y decisiones.
- Mantener una cola central de tareas (`work/WORK_QUEUE.md`).

## Principios

1. **Agentes por función, no por modelo.** Cada rol (Product Owner, Coordinator, Developer, Reviewer, Auditor, UX Designer) puede ser desempeñado por cualquier modelo o proveedor. Las asignaciones son flexibles y cambian según disponibilidad y contexto.
2. **Product Owner tiene autoridad de alcance.** Solo el PO puede aprobar cambios de alcance, nuevas fases o acciones destructivas.
3. **Coordinator organiza, no autoriza.** El coordinador asigna tareas, prioriza la cola y facilita handoffs, pero no aprueba cambios de alcance por su cuenta.
4. **Informes honestos.** Todo informe distingue: resultados comprobados, supuestos y tareas pendientes.
5. **Sistema simple.** Sin automatizaciones, CI/CD ni dependencias nuevas. Documentación y procesos manuales.

## Estructura

```
docs/factory/
├── README.md                    # Este archivo
├── roles/                       # Definición de roles
│   ├── product-owner.md
│   ├── coordinator.md
│   ├── developer.md
│   ├── reviewer.md
│   ├── auditor.md
│   └── ux-designer.md
├── workflow/                    # Flujos de trabajo
│   ├── feature-flow.md
│   ├── bug-flow.md
│   └── release-flow.md
├── templates/                   # Plantillas reutilizables
│   ├── issue-template.md
│   ├── pr-template.md
│   ├── test-report.md
│   ├── handoff-template.md
│   ├── ux-audit-template.md
│   ├── design-spec-template.md
│   └── independent-review-template.md
├── decisions/                   # Registro de decisiones
│   ├── adr-template.md
│   └── log.md
└── work/                        # Cola central de trabajo
    └── WORK_QUEUE.md
```

## Cómo usar este sistema

1. **Nueva tarea:** Crear entrada en `work/WORK_QUEUE.md` con rol responsable, estado y dependencias.
2. **Feature:** Seguir `workflow/feature-flow.md`. Usar plantillas de `templates/`.
3. **Bug:** Seguir `workflow/bug-flow.md`.
4. **Release:** Seguir `workflow/release-flow.md`.
5. **Decisión de arquitectura:** Usar `decisions/adr-template.md` y registrar en `decisions/log.md`.
6. **Handoff entre entregas:** Usar `templates/handoff-template.md`.

## Relación con documentos principales

| Documento | Relación |
|-----------|----------|
| `AGENTS.md` | Reglas permanentes del proyecto. Este directorio no las reemplaza. |
| `VISION.md`, `REQUIREMENTS.md`, etc. | Fuente de verdad del producto. La factory los respeta. |
| `SECURITY.md` | Obligatorio. Ningún rol puede debilitarlo. |
