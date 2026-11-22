# RESPONSIVE-002 — Corregir overflow horizontal móvil

**Prioridad:** P0 · **Responsable:** Developer — Mimo · **Estado:** READY  
**Rama:** product/lifeos-evolution · **Tipo:** corrección localizada, sin rediseño.

## Contexto y problema

STAB-001 y UX-REVIEW-001 registraron scroll horizontal no deseado a 390×844 en pantallas de Projects, Habits y Notes. En la revisión se identificó como posible causa la regla .main con margin auto dentro del contenedor flex de la aplicación. Home y Tasks ya fueron corregidas y no deben regresionar.

La causa debe reproducirse en la rama actual antes de modificar CSS; no asumir que el diagnóstico antiguo sigue siendo idéntico.

## Objetivo

Eliminar el overflow horizontal real en las vistas afectadas sin recortar contenido, bloquear el scroll legítimo ni alterar la composición de escritorio.

## Alcance

- Inspeccionar el layout shell y la regla de .main con el navegador.
- Corregir la causa en el contenedor o sus hijos; evitar parches locales repetidos.
- Comprobar Projects (listado y detalle), Habits, Notes, Home, Tasks y Settings.
- Mantener navegación, sidebar/menú móvil, formularios, tablas y modales operables.
- Registrar cualquier elemento que realmente necesite scroll horizontal propio (por ejemplo una tabla), con su contenedor limitado y evidente.

## No hacer

- No aplicar overflow-x:hidden global como solución.
- No reducir tipografía o contenido para esconder el problema.
- No reestructurar visualmente los módulos.
- No cambiar el token --text-muted ni otras decisiones de sistema visual abiertas.
- No introducir dependencias, endpoints, cambios de datos ni migraciones.

## Criterios de aceptación

1. En 390×844, document.documentElement.scrollWidth no supera clientWidth en las vistas principales salvo scroll interno intencional y documentado.
2. En 768×1024 y 1440×900 no se producen recortes ni desbordes nuevos.
3. No se ocultan botones, campos, textos, badges o contenido de tablas.
4. Los modales permanecen dentro del viewport; los formularios se pueden recorrer.
5. Scroll vertical y navegación táctil funcionan.
6. Home y Tasks no regresionan.
7. La consola no presenta errores nuevos.

## Pruebas

- Edge/Chromium en 1440×900, 768×1024 y 390×844.
- Theme dark y light.
- Probar Projects listado/detalle, Tasks, Habits, Notes, Home y Settings.
- Inspeccionar ancho de documentElement/body/main y elementos con bounding rect fuera del viewport.
- Ejecutar pytest, Ruff, node --check según archivos tocados, smoke con LIFEOS_DATA_DIR temporal y git diff --check.

## Entrega

Capturas o medidas antes/después, causa confirmada, archivos cambiados, pruebas exactas y resultados. Commit y push a product/lifeos-evolution. Estado REVIEW, no DONE.
