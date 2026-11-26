# Registro de decisiones — Life OS Factory

**Propósito:** Histórico de decisiones arquitectónicas y de producto.
**Mantenimiento:** Agregar una entrada por cada ADR aceptado.

---

## Formato de entrada

```
### ADR-XXX: [Título]
- **Fecha:** YYYY-MM-DD
- **Estado:** Aceptada / Rechazada / Reemplazada
- **Decidido por:** [Product Owner]
- **Archivo:** [link al ADR completo]
- **Resumen:** [una línea]
```

---

## Decisiones registradas

### ADR-001: Dirección visual Phase 8 (dark como identidad principal)
- **Fecha:** 2026-11-17
- **Estado:** Aceptada
- **Decidido por:** Product Owner
- **Archivo:** (documentada en AGENTS.md §2 y VISION.md)
- **Resumen:** Dark theme como identidad visual principal, con soporte para light y system.

### ADR-002: Estructura factory para coordinación de trabajo
- **Fecha:** 2026-11-20
- **Estado:** Aceptada
- **Decidido por:** Product Owner
- **Archivo:** docs/factory/README.md
- **Resumen:** Sistema de roles, flujos y plantillas para coordinar trabajo entre agentes. Agentes identificados por función, no por modelo.

---

### ADR-003: Grid persistente para la personalización de Home
- **Fecha:** 2026-11-22
- **Estado:** Aceptada
- **Decidido por:** Product Owner
- **Archivo:** docs/factory/decisions/ADR-003-home-widget-grid-layout.md
- **Resumen:** Extender las preferencias de widgets con spans validados y orden global en un grid responsive, manteniendo SQLite/API/exportación como fuentes persistentes.

*(Agregar nuevas entradas debajo de esta línea)*
