# PR: [Título de la funcionalidad o fix]

**Fecha:** YYYY-MM-DD
**Autor:** [Rol / Agente]
**Rama:** [nombre]
**Relacionado con:** [issue o tarea en WORK_QUEUE.md]

## Resumen

[Brevedes de qué cambia y por qué.]

## Cambios realizados

- Archivo 1: [qué cambió]
- Archivo 2: [qué cambió]

## Verificación

| Comando | Resultado |
|---------|-----------|
| `node --check` | ✅ / ❌ |
| `ruff check app tests` | ✅ / ❌ |
| `pytest -q` | ✅ / ❌ (N passed) |
| Smoke test | ✅ / ❌ |

## Resultados honestos

- **Comprobado:** [qué se verificó con pruebas reales]
- **Supuesto:** [qué se asume correcto sin prueba directa]
- **Pendiente:** [qué no se pudo verificar]

## Checklist

- [ ] No modifica backend sin autorización
- [ ] No modifica base de datos sin migración
- [ ] No incluye secretos ni datos personales
- [ ] Documentación actualizada si aplica
- [ ] `SECURITY.md` respetado
- [ ] No agrega dependencias nuevas
