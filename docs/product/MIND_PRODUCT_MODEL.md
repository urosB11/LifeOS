# Mind — Modelo de producto

**Versión:** 0.2  
**Estado:** dirección de producto aprobada por el PO; implementación incremental.  
**Fecha:** 22 de noviembre de 2026

## 1. Propósito

Mind es el entorno visual de pensamiento, conocimiento, trabajo, estudio e investigación de LifeOS. Permite capturar información, convertirla en contenido útil, organizarla espacialmente, relacionar conceptos y construir espacios de trabajo que evolucionan con el usuario.

**Prioridad fundamental: Mind debe ser una aplicación funcional y valiosa sin IA.** Las funciones esenciales —crear, editar, organizar, conectar, consultar, planificar y recuperar información— deben funcionar localmente y sin Orbes.

Mind no es:
- un chat que reemplaza la organización del conocimiento;
- un pizarrón infinito sin estructura ni persistencia;
- un gestor de tareas duplicado;
- una interfaz cuya utilidad dependa de un proveedor de IA.

## 2. Principio rector

El usuario piensa y trabaja; Mind permite capturar, explorar, organizar y construir; las herramientas inteligentes podrán colaborar más adelante; el usuario conserva el control.

## 3. Organización conceptual

- **Mind** es el entorno general.
- **Inbox** es una entrada transversal para capturas rápidas sin clasificar.
- **Spaces** son contextos flexibles: Personal, Research, Learning, proyectos u otros que defina el usuario.
- **Canvases** son superficies visuales dentro de un Space. Un Space puede contener varios Canvases.
- **Cards** son los elementos principales del Canvas. Pueden representar contenido propio de Mind, entidades de LifeOS o elementos puramente visuales.
- **Knowledge** es la biblioteca de contenido canónico, independiente de su posición o representación visual.

Los Spaces organizan contextos; no deben convertirse en carpetas rígidas que obliguen a duplicar información. Una misma pieza de contenido debe poder aparecer en más de un Canvas conservando una sola fuente de verdad.

## 4. El Canvas

El Canvas es libre por defecto. La estructura es opcional y el usuario puede organizarlo como mapa conceptual, tablero de proyecto, espacio de estudio, investigación, planificación o composición visual.

Capacidades progresivas:
- añadir, editar, mover, redimensionar y ordenar tarjetas;
- ampliar/reducir y desplazarse por el espacio;
- seleccionar y organizar grupos;
- conectar tarjetas visualmente;
- asignar significado a relaciones cuando corresponda;
- abrir el contenido completo sin perder el contexto del Canvas;
- guardar y recuperar los cambios;
- ofrecer navegación alternativa accesible a la representación espacial.

El Canvas no es el contenido: es una superficie que presenta y organiza objetos con identidad propia.

## 5. Cards: contenedor visual y contenido

Una Card tiene dos dimensiones que deben mantenerse separadas:

1. **Instancia visual en el Canvas:** identidad de la representación, Canvas al que pertenece, posición, tamaño, orden, estilo y estado visual.
2. **Contenido canónico:** información que la tarjeta muestra o referencia. No debe duplicarse por mover o reutilizar la tarjeta.

Una tarjeta puede ser sencilla o convertirse en un pequeño espacio de trabajo. No todas las tarjetas tienen que tener el mismo formato ni mostrar todos sus controles permanentemente.

### 5.1 Familias de tarjetas

- **Contenido nativo:** idea, nota, concepto, recurso o documento.
- **Documento:** contenido más extenso y estructurado, editable dentro de Mind.
- **Entidad LifeOS:** tarea, proyecto o hábito existente, mostrada mediante una referencia viva a su módulo canónico.
- **Fuente/recurso:** enlace, referencia bibliográfica o material de consulta.
- **Visual:** texto libre, forma, marco o agrupador sin entidad de dominio.
- **Media/embebido (etapa posterior):** imagen, archivo, audio, video u otro recurso, respetando la política local-first y de seguridad.

### 5.2 Contenido interno y bloques

Las tarjetas de contenido podrán evolucionar hacia documentos compuestos por bloques. La dirección funcional contempla:
- párrafos, títulos y subtítulos;
- listas numeradas y con viñetas;
- checklists y pasos;
- enlaces y referencias;
- tablas;
- campos estructurados e inputs cuando exista un caso de uso claro;
- contenido multimedia y embeds en una etapa posterior.

No todo bloque tiene que convertirse en una tarjeta independiente. Un documento puede contener muchos bloques y seguir siendo una sola pieza de contenido canónico.

**Decisión técnica pendiente antes de implementar documentos ricos:** comparar extender el modelo actual de Notes frente a introducir un modelo de documentos/contenido nativo de Mind. La decisión debe evitar dos fuentes de verdad paralelas, preservar las Notes existentes y permitir referencias desde varios Canvases. No almacenar contenido estructurado como HTML ejecutable ni introducir un editor/framework sin aprobación.

## 6. Usos que el producto debe soportar

### Proyectos y trabajo
Un Space o Canvas puede funcionar como espacio de trabajo de un proyecto: alcance, contexto, documentación, decisiones, recursos, tareas, dependencias, notas y seguimiento. Las tareas y proyectos siguen siendo entidades canónicas de LifeOS; Mind las presenta y conecta sin duplicarlas.

### Estudio y aprendizaje
El usuario puede construir mapas de conceptos, fichas, resúmenes, fuentes, ejercicios, checklists, planes de aprendizaje y secuencias de estudio. Puede conectar conceptos y visualizar relaciones. Este flujo debe ser realizable manualmente, sin IA.

### Investigación y pensamiento
El usuario puede reunir fuentes, registrar preguntas, comparar hipótesis, escribir documentos, construir relaciones y reorganizar el conocimiento a medida que aprende.

Estos son usos del mismo sistema de Cards, bloques, Spaces y Canvas; no requieren convertir cada actividad en un módulo separado.

## 7. Relaciones

Distinguir siempre:
- **Conexión visual:** línea entre dos instancias de tarjetas en un Canvas. Puede ser puramente gráfica.
- **Relación semántica:** relación con significado entre contenidos canónicos, independiente de la posición y reutilizable en varios Canvases.

Tipos semánticos iniciales candidatos: relacionado con, parte de, depende de, contribuye a, evidencia de, contradice y desarrolla. El catálogo se puede ampliar después de validar los casos de uso.

Un mind map es una forma opcional de organizar y visualizar conceptos sobre el Canvas; no debe ser un segundo almacén de contenido.

## 8. Búsqueda y biblioteca

- Búsqueda global en el contenido de Mind y, progresivamente, en entidades relacionadas de LifeOS.
- Búsqueda contextual dentro de un Space o Canvas.
- La biblioteca permite encontrar el contenido canónico, abrirlo y agregar nuevas representaciones sin copiarlo.
- Un resultado debe poder llevar al objeto original y a sus ubicaciones relevantes.

## 9. Integración con LifeOS

Tasks, Projects y Habits mantienen sus propios modelos, servicios y reglas. Una Card puede mostrar una entidad existente y ofrecer acciones soportadas por su API. Por ejemplo, crear una tarea desde un contexto de proyecto debe llamar al servicio canónico de Tasks y conservar sus validaciones.

Mind no crea una segunda tabla de tareas/proyectos/hábitos ni redefine su estado. Los objetivos u otras entidades futuras solo se integrarán cuando existan en el producto y tengan contrato aprobado.

## 10. Orbes e IA: evolución posterior, no dependencia

Los Orbes son una capa opcional futura. La primera implementación de Mind no requiere modelos, proveedores, prompts, herramientas inteligentes ni servicios remotos.

La visión futura contempla una acción contextual por tarjeta que abre un mini-chat asociado a esa tarjeta; también puede trabajar con una selección, grupo, Space o Canvas. Puede consultar, resumir, analizar, generar informes y preparar operaciones. El modelo detallado está en `ORBES_MODEL.md`.

Ninguna función básica de Mind debe bloquearse por la ausencia, saturación, costo o indisponibilidad de IA.

## 11. Local-first, seguridad y propiedad de datos

- Las funciones esenciales operan sin Internet.
- Los datos canónicos se guardan localmente y tienen una fuente de verdad clara.
- Exportación, backup y restauración se contemplan desde la primera entrega que persiste datos.
- Los embeds remotos no se cargan automáticamente; requieren una acción/consentimiento claro y deben explicar que necesitan conexión.
- El contenido de tarjetas se trata como dato no confiable; no se ejecuta HTML/JavaScript de usuario.
- No se envía contenido a servicios externos por defecto.
- Toda acción destructiva conserva las políticas de confirmación y preservación del contenido.

## 12. Principios de experiencia

- Captura rápida desde cualquier contexto relevante.
- Canvas libre, con estructura opcional.
- Edición contextual e inline para cambios breves; editor amplio para documentos.
- Las tarjetas revelan controles cuando son útiles, evitando convertir el Canvas en una grilla de botones.
- El contenido debe seguir siendo legible y editable en móvil; las interacciones espaciales tendrán alternativas táctiles y accesibles.
- Guardado fiable, estados de error explícitos y recuperación de borradores.
- La densidad, jerarquía y consistencia deben acompañar el trabajo real, no la decoración.

## 13. Límites del primer MVP

El primer MVP es una base funcional de Spaces, Inbox, Canvas y Cards de texto simples con persistencia. No incluye Orbes, voz, IA, embeds remotos, editor documental avanzado, colaboración, sincronización cloud ni autonomía.

La riqueza del producto se incorpora en entregas sucesivas sin rehacer el modelo de contenido y representación.
