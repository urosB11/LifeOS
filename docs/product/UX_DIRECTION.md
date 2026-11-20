# Dirección de experiencia e interfaz — LifeOS

**Versión:** 0.1 · **Fecha:** 20 de noviembre de 2026

## Objetivo

La interfaz debe sentirse como un centro de operaciones personal: calma, precisa, técnica, contemporánea y útil. La estética no debe ocultar información ni convertir cada dato en una tarjeta.

## Principios UX

1. **Jerarquía antes que decoración.** La información urgente o accionable destaca más que los totales generales.
2. **Densidad útil.** Mostrar suficiente información para decidir sin desperdiciar espacio ni reducir legibilidad.
3. **Acción contextual.** Crear o modificar una tarea desde el proyecto donde el usuario trabaja.
4. **Captura rápida.** Registrar tareas y notas con pocos campos obligatorios; lo opcional no debe bloquear.
5. **Progresión visible.** Usar barras, matrices, calendarios y gráficos cuando aporten una lectura real.
6. **Consistencia.** Mismos patrones para formularios, botones, estados, filtros, vacíos y confirmaciones.
7. **Responsive real.** Reorganizar acciones y jerarquía para móvil; no solo encoger el escritorio.
8. **Accesibilidad.** Teclado, foco visible, contraste, semántica y errores asociados.
9. **Claridad analítica.** Cada cifra debe explicar qué mide y qué no mide.
10. **No sobrecargar.** Evitar paneles de métricas iguales, gráficos sin historia y tarjetas anidadas.

## Lenguaje visual vigente

El repositorio tiene tokens CSS en frontend/assets/css/vars.css:
- tema oscuro como identidad principal actual;
- tema claro como alternativa;
- verde petróleo/teal como acento;
- superficies diferenciadas, texto legible y bordes sutiles;
- radios moderados, sombras discretas y transiciones cortas.

Los componentes compartidos viven en frontend/assets/css/components.css. Reutilizar tokens y clases existentes antes de agregar variantes.

No cargar fuentes ni imágenes remotas para la interfaz esencial. Mantener funcionamiento offline.

## Reglas de composición

- Una acción primaria por contexto.
- Reservar rojo para acciones destructivas o errores.
- No usar color de éxito para cualquier dato positivo.
- Reducir tarjetas redundantes; agrupar información relacionada.
- Preferir listas densas y legibles para elementos repetitivos.
- Mostrar estados vacíos con una acción útil.
- Usar gráficas solo si existen datos suficientes y una lectura que no pueda expresarse mejor con una lista.

## Comportamientos

- Los formularios no desaparecen ante un error de red o validación.
- Los botones muestran estado de envío y previenen doble submit.
- Tras una acción exitosa, actualizar áreas afectadas sin perder contexto.
- Las acciones destructivas se separan visualmente.
- Los filtros se conservan al actualizar listas cuando corresponda.
- Los paneles de detalle tienen retorno y navegación accesibles.

## Dirección de Home

Home debe responder en orden:
1. qué requiere atención;
2. qué puedo hacer hoy;
3. qué proyectos necesitan seguimiento;
4. cómo vienen los hábitos de hoy;
5. cómo capturo una tarea o nota.

La grilla de seis métricas iguales no debe seguir dominando. La configuración de widgets se conserva, pero el diseño inicial debe ser útil sin personalización.

## Validación visual mínima

Revisar cada pantalla modificada a:
- escritorio: 1440 × 900;
- tablet: 768 × 1024;
- móvil: 390 × 844.

Comprobar teclado, foco, estados vacío/error/carga, overflow horizontal y textos largos.