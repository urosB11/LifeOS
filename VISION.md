# Life OS — Visión del producto

**Versión:** 0.4 · **Fecha:** 21 de noviembre de 2026

## Visión
Life OS es un sistema operativo personal local-first: un centro de operaciones que conecta prioridades, objetivos, proyectos, tareas, hábitos, conocimiento y análisis en una experiencia coherente. No debe ser una colección de CRUD ni un dashboard decorativo. Conecta el ciclo **intención → planificación → ejecución → evidencia → aprendizaje → ajuste**.

## Problema
La información y las acciones personales se dispersan entre calendarios, listas, notas, hojas de cálculo y servicios. Esto dificulta decidir qué requiere atención, conectar objetivos con acciones, recuperar contexto, medir evolución y automatizar sin perder control.

## Promesa
Al abrir Life OS, el usuario puede responder qué requiere atención, qué es importante ahora, qué resultados están en marcha, cómo evolucionan sus hábitos, qué cambió y qué necesita registrar.

## Modelo conceptual
| Concepto | Responsabilidad | Estado |
|---|---|---|
| Área | Contexto amplio de vida/trabajo | Futuro |
| Objetivo | Resultado deseado, medible cuando corresponda | Futuro |
| Proyecto | Esfuerzo finito orientado a un resultado | Actual |
| Hito/entregable | Resultado parcial verificable | Futuro |
| Tarea | Acción concreta | Actual |
| Hábito | Práctica recurrente registrada | Actual |
| Nota/idea/recurso | Información, conocimiento o contexto | Actual / evolución |
| Evento | Cambio relevante | Básico |
| Métrica | Cálculo reproducible | Parcial |

Relación conceptual futura: Área → Objetivo → Proyecto → Hitos/entregables → Tareas. No crear entidades anticipadas sin flujo funcional.

**Distinciones:** actividad no es resultado; tarea completada no implica entregable aceptado; progreso de tareas no equivale a progreso del resultado; finalizar un proyecto es una decisión explícita.

## Módulos
Home (centro diario), Tasks (acciones), Projects (resultados finitos), Habits (consistencia), Notes (conocimiento), Analytics/Reports (evolución). En el futuro: Goals, Mind, Work, Business, Finance, AI Orchestrator e Integrations.

## Experiencia central
Home prioriza atención, plan del día, proyectos relevantes, hábitos y captura rápida. Los módulos son espacios de trabajo y permiten acciones contextuales, como crear tareas desde un proyecto. Formularios progresivos, compactos y resilientes. Gráficas solo cuando los datos y la lectura aporten valor.

## Mind — entorno de pensamiento y conocimiento
Mind será el entorno para capturar, explorar, desarrollar, relacionar y estructurar ideas, notas, recursos e investigaciones. Su experiencia combinará espacios de trabajo, lienzos libres (Canvas), conocimiento reutilizable y asistencia contextual mediante Orbes.

Mind no es solamente un pizarrón ni un chat. El Canvas permite pensar visualmente; los contenidos mantienen identidad propia y pueden aparecer en varios lienzos sin duplicarse. Las relaciones semánticas entre contenidos no dependen de su posición visual. La captura debe ser rápida y no obligar a convertir cada pensamiento en una tarea o proyecto.

Los Orbes son sesiones de trabajo inteligentes vinculadas a un objeto, grupo o espacio. Funcionan como minichats contextuales capaces de investigar, analizar, sintetizar, cuestionar, organizar y producir artefactos —por ejemplo informes, resúmenes, gráficos, métricas o mapas— que pueden incorporarse al lienzo y reutilizarse. Pueden ser temporales o persistentes. Su contexto parte de una selección explícita y puede ampliarse con autorización. La política de permisos es global, con ajustes particulares por Orbe dentro de esos límites. Observar y proponer son capacidades distintas de aplicar cambios: las operaciones sobre Canvas o entidades canónicas requieren vista previa y aprobación explícita.

La especificación funcional está en `docs/product/MIND_PRODUCT_MODEL.md` y `docs/product/ORBES_MODEL.md`. Esta visión no autoriza todavía implementación ni proveedores de IA.

## Analítica
Tres niveles: estado actual, evolución temporal y resultados. Cada métrica documenta fórmula, fuente, período, zona horaria, faltantes y limitaciones. No inventar datos ni reconstruir historia sin eventos fiables. Mind puede visualizar análisis de conocimiento o de datos vinculados; Analytics conserva la responsabilidad sobre las métricas longitudinales del desempeño personal.

## IA y agentes (futuro)
La IA será opcional. Podrá consultar contexto autorizado, analizar, proponer objetivos y planes, mostrar preview y ejecutar solo acciones aprobadas mediante herramientas tipadas. No SQL arbitrario ni permisos irrestrictos. Los Orbes son la experiencia contextual de interacción; no son en sí mismos modelos ni agentes. El usuario conserva autoridad.

## Principios
Utilidad primero; jerarquía antes que decoración; fuente de verdad única; propiedad y portabilidad de datos; control humano; local-first; simplicidad técnica; evolución incremental; privacidad por defecto; interoperabilidad futura.

## Dirección técnica
Se mantiene frontend HTML/CSS/JS nativo, FastAPI, SQLAlchemy, SQLite y Alembic en monolito modular local. Esta visión no autoriza frameworks, microservicios, cloud, sync, agentes runtime ni acceso remoto.

## Evolución
0.1 núcleo personal; 0.2 hábitos; Fase 8 consolidación UX; Fase 9 experiencia diaria; Fase 10 modelo de planificación y resultados; Fase 11 Analytics e historial; Fase 12 Mind (fundación de conocimiento y Canvas); Fase 13 Work/Business/Finance según necesidad; Fase 14 AI Orchestrator y Orbes operativos; Fase 15 integraciones y acceso remoto seguro. Primero experiencia y calidad de datos; después agentes e integraciones.

## Éxito
El usuario identifica prioridades rápido, captura desde contexto, conecta tareas/proyectos/objetivos sin duplicación, distingue actividad de resultados, entiende métricas y recupera sus datos. En Mind, puede desarrollar una idea desde captura hasta conocimiento o artefacto reutilizable sin perder su contexto ni ceder el control a la IA.

## Fuera de alcance inmediato
Objetivos/áreas/hitos como entidades, Analytics histórico, implementación de Mind, IA runtime, integraciones, cloud, sync, multiusuario, App Center ejecutable y microservicios.

## Gobierno
La visión orienta; ROADMAP.md y WORK_QUEUE.md autorizan trabajo. Toda entidad, métrica o integración nueva requiere especificación, impacto y aprobación. SECURITY.md prevalece en seguridad.
