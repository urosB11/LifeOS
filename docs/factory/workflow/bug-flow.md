# Flujo: Bug (Corrección de defecto)

**Propósito:** Guía para identificar, corregir y verificar defectos.

## Estados

```
REPORTED → TRIAGED → FIXING → VERIFIED → CLOSED
```

## Pasos

### 1. REPORTED
- Cualquier rol puede reportar usando `templates/issue-template.md`.
- Registrar en `work/WORK_QUEUE.md` con prioridad.

### 2. TRIAGED
- Coordinator clasifica severidad:
  - **Crítico:** Rompe funcionalidad esencial o seguridad.
  - **Importante:** Afecta experiencia significativamente.
  - **Menor:** Cosmético o edge case.
- Product Owner decide si se corrige ahora o se pospone.

### 3. FIXING
- Developer implementa corrección.
- Si el fix requiere cambio de esquema → migración versionada + pruebas + actualización `DATABASE.md`.
- Si el fix debilita seguridad → rechazar y escalar al PO.

### 4. VERIFIED
- Reviewer verifica:
  - El fix resuelve el problema original.
  - No introduce regresiones.
  - Pruebas pasan (pytest, node --check, ruff).

### 5. CLOSED
- PO aprueba.
- Coordinator actualiza cola de trabajo.
- Developer commit + push (con autorización).

## Reglas

- Nunca usar la base personal para pruebas destructivas.
- Nunca hacer `git reset --hard` sin autorización.
- Si el bug es de seguridad → escalar inmediatamente al PO.
