# Life OS — Vision del producto

**Estado:** línea base de producto aprobada para el MVP 0.1  
**Versión:** 0.2  
**Fecha:** 17 de noviembre de 2026  
**Tipo de documento:** visión y dirección del producto

> Este documento describe qué queremos construir y por qué. No es todavía una especificación técnica definitiva ni una autorización para comenzar a programar.

## 1. Visión

Life OS es un centro de operaciones personal: una aplicación modular que reúne información, herramientas y actividades de distintas áreas de la vida en una experiencia coherente.

Su punto de entrada es un dashboard configurable compuesto por widgets. El usuario puede consultar lo importante, registrar información y acceder a las herramientas que necesita sin tener que saltar constantemente entre aplicaciones desconectadas.

A largo plazo, Life OS podrá integrar servicios externos, aplicaciones propias y capacidades de inteligencia artificial. Sin embargo, su utilidad básica no debe depender de una conexión a Internet ni de un modelo de IA.

## 2. Problema que buscamos resolver

La información y las actividades personales suelen quedar repartidas entre calendarios, listas de tareas, notas, hojas de cálculo, correos y aplicaciones diferentes. Esto dificulta:

- mantener una visión general de lo que requiere atención;
- conectar objetivos, proyectos y tareas;
- recuperar ideas e información importante;
- seguir el trabajo, los proyectos y las finanzas desde un mismo lugar;
- automatizar actividades sin perder el control de los datos y las decisiones.

Life OS busca reducir esa fragmentación y ofrecer un entorno que pueda crecer junto con las necesidades de su usuario.

## 3. Usuarios y alcance

### Usuario inicial

La primera versión se diseña para uso personal, local y de un solo usuario. El objetivo es resolver necesidades reales del propio usuario antes de intentar convertir el sistema en un producto multiusuario.

### Dirección futura

La arquitectura debe evitar dependencias innecesarias que impidan evolucionar hacia acceso remoto, sincronización o múltiples usuarios. Esto no significa implementar esas capacidades en la primera versión ni anticipar complejidad que todavía no necesitamos.

## 4. Organización funcional prevista

Los nombres y límites de estos módulos pueden evolucionar. Esta es la organización conceptual de referencia:

| Área | Responsabilidad |
|---|---|
| **Home** | Prioridades, agenda, tareas relevantes y resumen del día. Es una vista de síntesis, no una copia de todos los módulos. |
| **Work** | Búsqueda laboral, CV, portfolio, postulaciones, entrevistas y seguimiento. |
| **Business** | Proyectos comerciales, clientes, servicios, productos, ventas e ingresos. |
| **Finance** | Cuentas, movimientos, gastos, presupuestos y objetivos financieros. |
| **Mind** | Notas, conocimiento, ideas, hábitos, objetivos y planificación personal. |
| **Estadísticas e informes** | Capacidad transversal para medir, analizar y presentar la evolución de las distintas áreas, con indicadores globales y métricas específicas de cada módulo. |
| **App Center** | Catálogo para descubrir, habilitar y configurar widgets, aplicaciones e integraciones. |
| **AI Orchestrator** | Capa transversal que, en etapas futuras, conectará modelos, memoria, herramientas y agentes. |

### Alcance de la primera versión

La versión 0.1 será más pequeña que esta visión completa. Se centrará en:

- Home y su dashboard;
- tareas;
- proyectos;
- notas;
- configuración básica de widgets;
- persistencia y exportación de datos.

Work, Business, Finance y Mind se desarrollarán progresivamente. En la versión inicial, las tareas, los proyectos y las notas cubrirán una parte pequeña pero útil de esas necesidades.

## 5. Experiencia central

La experiencia debe organizarse alrededor de un dashboard compuesto por widgets. Un widget es una unidad de interfaz que presenta información o permite realizar una acción concreta.

En la versión 0.1:

- el dashboard incluirá widgets internos desarrollados como parte de la aplicación;
- el usuario podrá mostrar u ocultar widgets y cambiar su orden;
- la configuración se conservará al cerrar y volver a abrir la aplicación;
- los widgets mostrarán información procedente de las mismas fuentes de datos que las secciones de tareas, proyectos y notas.

En versiones posteriores, el App Center podrá ampliar este modelo con módulos, integraciones y aplicaciones instalables. La versión 0.1 **no** implementará todavía un sistema general de instalación o ejecución de plugins de terceros.

La experiencia también deberá ofrecer una capa de estadísticas e informes: Home podrá mostrar indicadores destacados y cada área tendrá, a medida que se implemente, vistas de seguimiento y análisis propias. La información no debe limitarse al estado actual; cuando resulte relevante, se conservará el historial de cambios para analizar evolución, tendencias y resultados a lo largo del tiempo.

## 6. Estadísticas, seguimiento e informes

Las estadísticas y los informes son una capacidad central de Life OS, no un complemento exclusivo de Finance ni una función dependiente de la inteligencia artificial. El sistema deberá permitir comprender qué está ocurriendo, cómo evoluciona cada área y si las acciones están acercando al usuario a sus objetivos.

La capacidad analítica será transversal y abarcará, según los datos disponibles en cada módulo:

- **Visión global:** actividad, prioridades, evolución y cumplimiento de objetivos en el conjunto de Life OS.
- **Work:** postulaciones, etapas de selección, entrevistas, respuestas, tiempos y resultados.
- **Business:** proyectos, clientes, ventas, ingresos, actividad comercial y cumplimiento de objetivos.
- **Finance:** ingresos, gastos, saldos, presupuestos, ahorro, flujo de dinero y evolución financiera.
- **Mind:** hábitos, consistencia, objetivos, planificación y evolución de las prácticas registradas.
- **Projects y Tasks:** tareas creadas y completadas, avance, vencimientos, carga de trabajo y evolución de proyectos.

Los informes deberán poder evolucionar hacia filtros por período, módulo, proyecto, categoría y otros criterios pertinentes; comparación entre períodos; indicadores clave; tendencias y exportación. Cada métrica deberá tener una definición comprensible, una fórmula o criterio de cálculo identificable y una fuente de datos trazable. No se presentarán estimaciones como datos reales ni se inferirán resultados cuando falte información.

La profundidad de los informes crecerá junto con los módulos. Desde las primeras versiones, el diseño de datos deberá conservar las fechas y los cambios de estado necesarios para reconstruir la evolución. La versión 0.1 podrá ofrecer indicadores básicos de tareas y proyectos, pero no necesita implementar todavía el centro analítico completo.

## 7. Principios rectores

Toda decisión de producto y tecnología debe evaluarse frente a estos principios:

1. **Portabilidad:** evitar dependencias tecnológicas o de proveedores que generen bloqueos innecesarios. Mantener una ruta razonable para cambiar componentes.
2. **Propiedad de los datos:** los datos pertenecen al usuario. Deben poder respaldarse y exportarse a formatos abiertos y documentados.
3. **Seguridad:** proteger datos y secretos; aplicar permisos mínimos; no conceder autonomía irrestricta a la IA.
4. **Modularidad:** cada área y funcionalidad debe poder desarrollarse, probarse y modificarse con el menor acoplamiento posible.
5. **Simplicidad:** incorporar una tecnología solo cuando resuelva un problema real. Evitar complejidad prematura.

Principios complementarios:

- **Utilidad sin IA:** las funciones esenciales deben seguir funcionando aunque no haya modelo de IA disponible.
- **Control del usuario:** las acciones externas o sensibles requerirán autorización explícita.
- **Transparencia:** los errores, las operaciones y las limitaciones del sistema deben ser comprensibles.
- **Evolución incremental:** cada versión debe entregar una mejora funcional verificable.

## 8. Dirección tecnológica (propuesta, no contrato definitivo)

La dirección inicial propuesta es una aplicación web responsive, ejecutada localmente durante el desarrollo y preparada para una eventual migración a un entorno online.

| Componente | Tecnología candidata | Responsabilidad |
|---|---|---|
| Interfaz | HTML, CSS y JavaScript | Dashboard y navegación |
| Backend | Python + FastAPI | API y lógica del sistema |
| Base de datos | SQLite | Persistencia local |
| IA | Capa desacoplada con modelos intercambiables | Razonamiento y generación, en etapas futuras |
| Agentes | Herramientas y servicios Python | Ejecución controlada de tareas, en etapas futuras |
| Desarrollo | OpenCode + Git | Construcción, revisión y mantenimiento |

La arquitectura candidata es un **monolito modular**, con separación clara entre interfaz, API, lógica de negocio y persistencia. No se propone comenzar con microservicios.

Las tecnologías concretas, bibliotecas, estructura de carpetas y estrategia de despliegue se definirán en el documento de arquitectura. Las opciones de alojamiento gratuito deberán verificarse cuando llegue el momento: no se asumirá que un servicio gratuito ofrece disponibilidad permanente o almacenamiento persistente.

## 9. Estrategia de evolución

### Versión 0.1 — Núcleo personal

Dashboard, tareas, proyectos, notas, widgets internos configurables, almacenamiento persistente y exportación/backup.

### Etapa 2 — Gestión personal

Agenda, objetivos, hábitos y mejoras de organización del conocimiento.

### Etapa 3 — Work y Business

CV, portfolio, vacantes, postulaciones, clientes y seguimiento de proyectos comerciales.

### Etapa 4 — Finance

Cuentas, movimientos, presupuestos, informes y objetivos financieros. Requiere especial atención a privacidad, seguridad y validación de cálculos.

### Etapa 5 — Estadísticas e informes transversales

Construir el espacio analítico de Life OS con indicadores globales, informes por módulo, filtros por período, comparaciones, tendencias, objetivos y exportación. Las métricas se habilitarán progresivamente según la madurez y calidad de los datos de cada área. La capa analítica deberá apoyarse en datos verificables y definiciones documentadas. Esta capacidad no dependerá de la IA y podrá desarrollarse antes o en paralelo con ella.

### Etapa 6 — Inteligencia artificial

Asistente conversacional, memoria y herramientas. Los agentes comenzarán con permisos de consulta y preparación; la ejecución de acciones requerirá autorización.

### Etapa 7 — Integraciones y acceso remoto

Integraciones como Gmail, Google Calendar, Telegram y GitHub, además de acceso desde otros dispositivos y posible sincronización. Cada integración se incorporará según necesidad y con permisos explícitos.

El orden puede ajustarse por aprendizaje y utilidad; las etapas no son fechas prometidas.

## 10. Cómo mediremos el éxito inicial

La versión 0.1 será satisfactoria cuando el usuario pueda:

1. abrir la aplicación localmente desde su computadora;
2. crear, editar, completar y consultar tareas;
3. crear proyectos y vincularles tareas;
4. crear, editar y recuperar notas;
5. personalizar los widgets visibles y su orden;
6. cerrar y volver a abrir la aplicación sin perder información;
7. generar una exportación o respaldo de sus datos y comprender cómo recuperarlos.

También debe poder utilizar las funciones principales sin conexión a Internet y sin configurar un proveedor de IA.

## 11. Fuera de alcance por ahora

No forman parte de la versión 0.1:

- agentes autónomos o ejecución de acciones externas;
- conexión con Gmail, Google Calendar, Telegram, GitHub u otros servicios;
- sincronización entre dispositivos o alojamiento público;
- cuentas multiusuario y colaboración;
- gestión financiera avanzada;
- centro completo de estadísticas e informes para todas las áreas (se incorporará progresivamente; la arquitectura deberá permitirlo);
- búsqueda laboral automatizada;
- marketplace o instalación dinámica de plugins de terceros;
- microservicios, Kubernetes o infraestructura distribuida;
- aplicación móvil nativa independiente.

## 12. Riesgos y respuestas

| Riesgo | Respuesta de diseño |
|---|---|
| Intentar abarcar demasiados módulos | Limitar el MVP y revisar el alcance por versión. |
| Agregar complejidad antes de necesitarla | Preferir un monolito modular y dependencias mínimas. |
| Perder datos | Diseñar exportación y respaldo desde el inicio y probar su recuperación. |
| Quedar atado a un proveedor | Separar las interfaces de servicios externos y modelos de IA. |
| IA con permisos excesivos | Separar consulta, preparación y ejecución; exigir autorización para acciones sensibles. |
| Rendimiento limitado del equipo | Evitar procesos y modelos pesados persistentes; ejecutar componentes bajo demanda. |

## 13. Decisiones futuras

Las decisiones que afectan al MVP local quedan registradas en `ARCHITECTURE.md`, `DATABASE.md`, `REQUIREMENTS.md` y `SECURITY.md`. No bloquean el inicio de la primera fase de desarrollo.

Siguen abiertas para etapas posteriores:

- si conviene empaquetar la aplicación como PWA o aplicación de escritorio;
- autenticación y autorización para un eventual acceso remoto o multiusuario;
- sincronización, resolución de conflictos y estrategia de alojamiento;
- proveedores y permisos de integraciones externas;
- límites y modelo de permisos de la capa de IA y los agentes.

---

**Regla de cambio:** cualquier cambio importante de visión o alcance debe reflejarse en este documento y en los requisitos relacionados antes de convertirse en trabajo de desarrollo. La visión completa no autoriza a implementar de una vez todos los módulos futuros.
