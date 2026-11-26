# ADR-003: Grid persistente para la personalización de Home

- **Fecha:** 2026-11-22
- **Estado:** Aceptada
- **Decidido por:** Product Owner
- **Archivo:** `docs/factory/decisions/ADR-003-home-widget-grid-layout.md`

## Contexto

La personalización existente guarda visibilidad y orden, pero asigna cada widget a una zona fija en código. No puede persistir tamaños ni un orden global responsive. El Product Owner aclaró que la nueva superficie es Home y autorizó extender modelo/API y añadir una migración. Projects y Notes quedan fuera.

## Decisión

Home utilizará un único CSS Grid auto-colocado. La preferencia persistida conserva el orden lineal global (`position`) y añade `column_span` (2–6) y `row_span` (1–3). Los spans son unidades de grid, no píxeles. La grilla cambia de seis columnas en escritorio a cuatro en tablet y una en móvil; los tamaños se adaptan al viewport sin alterar los valores guardados.

`widget_preferences` es la fuente de verdad. Se extiende mediante migración Alembic y el contrato existente GET/PUT `/api/v1/dashboard/widgets`. La exportación JSON sube de versión. No se usa `config_json` para layout ni `localStorage` como segunda fuente de preferencias.

`quick_add_task` y `quick_add_note` siguen siendo preferencias de visibilidad separadas, pero la tarjeta visual que agrupa ambas acciones comparte posición y spans.

## Alternativas descartadas

- **Coordenadas absolutas/píxeles:** crean solapamientos, dependen del viewport y requieren gestión compleja de colisiones.
- **Mantener zonas fijas:** no permite ubicación global ni tamaños personalizados.
- **`config_json` o `localStorage`:** no ofrecen un contrato de layout validable y documentado con exportación/backup coherentes.
- **Dependencia de layout externa:** innecesaria para seis widgets y contraria al stack nativo aprobado.

## Consecuencias

- Se requiere migración con valores por defecto y transformación determinista de preferencias existentes.
- El backend debe validar los spans y preservar spans existentes al recibir PUTs antiguos que no los incluyan.
- El frontend calcula la colocación desde orden y tamaño; el flujo auto-colocado evita solapamientos y permite adaptación responsive.
- La interacción ocurre solo en Personalizar y solo desde asas; las acciones internas conservan eventos y scroll normales.
