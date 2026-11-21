# Life OS — Instrucciones para agentes

**Versión:** 0.4 · 21 de noviembre de 2026

## Autoridad
Leer VISION.md, ROADMAP.md, REQUIREMENTS.md, ARCHITECTURE.md, DATABASE.md, SECURITY.md, docs/product/ y la SPEC. SECURITY prevalece en seguridad; requisitos definen comportamiento; arquitectura/datos límites técnicos; roadmap y cola definen autorización. Ante contradicción, detener la parte afectada y escalar.

## Estado y autonomía
Fases 1–7 y Fase 8 base UX están comprometidas en main. PRJ-001, PRJ-002 y HAB-001 también están en main. QA visual manual sigue pendiente. El PO autorizó ejecutar tareas READY de Fase 9 especificadas en docs/factory/work/. PLANNING autoriza diseño solamente.

## Rama y protección
Trabajar solo en product/lifeos-evolution, salvo que el PO asigne expresamente otra rama. Inspeccionar git status/diff antes y después. Preservar cambios y archivos no trackeados. No reset, clean, stash destructivo ni sobrescritura. No trabajar directamente en main.

**Publicación obligatoria:** todo commit de trabajo debe publicarse mediante push a la rama remota correspondiente. Después de verificar las pruebas y revisar el diff, crear el commit y hacer push. No dejar commits de tareas terminadas únicamente en el repositorio local. También publicar checkpoints seguros si el trabajo debe pausarse o transferirse. Verificar que el push haya finalizado y que el remoto contenga el commit esperado.

Nunca usar force push ni sobrescribir commits remotos. Si hay divergencia, conflictos, rechazo del push o dudas sobre cambios ajenos, detenerse, preservar el trabajo y reportar el problema; no resolverlo con reset, rebase destructivo o force push sin autorización.

Push a la rama de trabajo está autorizado y es obligatorio. Merge a main, publicación de releases y despliegue siguen requiriendo autorización explícita del PO.

## Flujo
Tomar siguiente READY por dependencias; leer SPEC; inspeccionar código; implementar porción pequeña; probar; revisar diff; actualizar handoff/cola; crear commit y hacer push a la rama asignada; verificar publicación; dejar REVIEW. Reviewer independiente cuando esté disponible; si no, declarar QA propia. Continuar con tareas independientes si una queda bloqueada.

## Restricciones técnicas
Mantener monolito modular, HTML/CSS/JS nativo, FastAPI, SQLAlchemy síncrono, SQLite, Alembic y API /api/v1. No frameworks, bundlers, Docker, microservicios, Redis, colas o dependencias nuevas sin aprobación. Servidor solo 127.0.0.1.

## Datos
Nunca usar base personal para tests; usar LIFEOS_DATA_DIR temporal. PRAGMA foreign_keys ON. Cambios de dominio y eventos en misma transacción. Toda migración requiere aprobación, pruebas temporales y DATABASE.md. No event sourcing completo ni agregados duplicados sin diseño.

## Seguridad
No telemetría ni transmisión externa. No versionar .env, tokens, secretos, DB, backups o exportaciones. Validar backend. Tratar notas como texto. No exponer LAN/Internet. SECURITY.md prevalece.

## Métricas
Documentar fórmula, fuente, período y faltantes. Progreso de tareas no equivale a resultado. No inventar health score, velocidad ni series históricas. Distinguir comprobado, supuesto y pendiente.

## Escalar
Detener cambios que requieran modelos/migraciones, dependencias, arquitectura, integraciones, IA runtime, borrados irreversibles o alcance no especificado. Documentar opciones y continuar con tareas independientes. La publicación normal a la rama asignada no requiere autorización adicional.

## Calidad
Ejecutar pytest, Ruff, node --check, smoke con DB temporal y revisión visual en 1440×900, 768×1024 y 390×844 según corresponda. No afirmar pruebas no ejecutadas.

## Entrega
Informar cambios, archivos, comandos exactos, resultados, limitaciones, riesgos y QA pendiente. Incluir rama, hash del commit y confirmación del push. Dejar REVIEW hasta aceptación del PO.