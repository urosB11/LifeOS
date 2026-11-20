# Flujo: Release (Liberación de versión)

**Propósito:** Guía para preparar y publicar una versión.

## Estados

```
PREPARING → TESTING → APPROVED → PUBLISHED
```

## Pasos

### 1. PREPARING
- Coordinator verifica que todas las tareas de la fase están DONE en `work/WORK_QUEUE.md`.
- Developer ejecuta verificación completa:
  - `node --check` en todos los JS modificados.
  - `ruff check app tests`.
  - `pytest -q` (resultado esperado: todos pasan).
  - Smoke test del servidor (todos los archivos 200 OK).
  - Base personal intacta (migración correcta).

### 2. TESTING
- Reviewer realiza revisión independiente usando `templates/independent-review-template.md`.
- UX Designer (si aplica) verifica experiencia de usuario.
- Auditor verifica seguridad e integridad de datos.

### 3. APPROVED
- Product Owner revisa:
  - Todos los tests pasan.
  - No hay hallazgos críticos pendientes.
  - Documentación actualizada.
  - Los informes distinguen comprobado / supuesto / pendiente.
- PO autoriza commit y push.

### 4. PUBLISHED
- Developer hace commit con mensaje descriptivo.
- Developer hace push a `main`.
- Coordinator actualiza `work/WORK_QUEUE.md`.
- Si hay docs afectados → actualizar `ROADMAP.md`, `DATABASE.md`, etc.

## Checklist de release

- [ ] Todos los tests pasan (pytest, ruff, node --check).
- [ ] Smoke test completo (archivos estáticos + API).
- [ ] Base personal intacta.
- [ ] No hay secretos ni datos en el diff.
- [ ] Documentación actualizada.
- [ ] Reviewer aprobó.
- [ ] PO autorizó push.
