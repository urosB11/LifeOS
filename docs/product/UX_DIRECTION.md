# Dirección de experiencia e interfaz — LifeOS

**Versión:** 0.2 · **Fecha:** 22 de noviembre de 2026

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

## 11. Modelo de interacción: de formularios a objetos de trabajo

La interfaz debe permitir actuar sobre el objeto en su contexto. No se busca eliminar botones por una cuota estética ni esconder funciones importantes: se busca reducir pasos, duplicaciones y controles que obligan a traducir una intención simple en una operación administrativa.

- **Una superficie de trabajo por contexto.** Home organiza la atención diaria; cada módulo permite profundizar sin duplicar la fuente de verdad.
- **Personalización en contexto.** Los widgets se ordenan desde Home en un modo explícito. Settings no duplica el editor.
- **Revelado progresivo.** Los formularios de creación/edición compleja comienzan cerrados y se abren desde una acción clara. Los campos opcionales aparecen cuando son pertinentes.
- **Edición directa con límites.** La edición inline se reserva para cambios breves y reversibles. Los formularios de varios campos usan un panel o editor estable, con Guardar y Cancelar explícitos.
- **Acciones frecuentes visibles.** Completar una tarea y registrar un hábito no deben quedar escondidos en menús secundarios. Eliminar y otras acciones destructivas permanecen diferenciadas y confirmadas.
- **Estado visible y honesto.** Carga, vacío, error y éxito son estados diferentes. Un fallo de consulta nunca se representa como cero elementos. Los borradores sobreviven a errores.
- **Sin duplicación de información.** Una tarea no debe aparecer dos veces en el mismo resumen de Home. La presentación resume; los módulos de dominio siguen siendo la fuente de verdad.
- **Métricas con semántica.** Mostrar solo datos disponibles y con una lectura válida. Ejecución de tareas no equivale a resultado ni a salud de un proyecto.
- **Movimiento con propósito.** Usar transiciones breves para comunicar cambios de estado o posición; no agregar animaciones continuas ni movimiento decorativo. Respetar prefers-reduced-motion.
- **Accesibilidad equivalente.** Toda interacción por arrastre debe tener alternativa por botones/teclado, foco conservado y anuncio de resultado. No depender de hover ni del color.

## 12. Alcance de personalización del dashboard

La primera entrega utiliza las zonas de layout que ya existen en Home y el campo position que ya persiste la API. Un widget puede cambiar de orden dentro de su zona, pero no cruzar de zona. El catálogo conserva IDs estables y la visibilidad de cada widget permanece independiente.

La Captura rápida se presenta visualmente como un grupo para mantener juntas las acciones de tarea y nota; sus dos preferencias de visibilidad siguen siendo independientes. El grupo se mueve como una sola unidad cuando al menos una de sus acciones está visible.

El movimiento entre zonas queda fuera de esta entrega. Antes de habilitarlo se debe decidir el modelo de layout, persistir la zona de forma explícita y actualizar DATABASE.md, el contrato de API, exportación y pruebas mediante una tarea y aprobación separadas. config_json no es un sustituto de ese diseño.

## 13. Patrones compartidos

| Intención | Patrón |
|---|---|
| Acción frecuente y reversible | Acción visible sobre el elemento, con feedback inmediato. |
| Cambio breve | Edición inline con Guardar/Cancelar; Enter confirma y Escape descarta. |
| Edición con varios campos | Panel/editor progresivo; conserva borrador y devuelve el foco al cerrar. |
| Acción ocasional | Menú contextual accesible con nombre y foco. |
| Acción destructiva | Separada de la acción primaria y confirmada explícitamente. |
| Reordenamiento | Modo Personalizar, asa explícita, vista previa, Guardar/Cancelar y alternativa mover arriba/abajo. |
| Error de guardado | Mensaje asociado al contexto, borrador preservado y reintento disponible. |
