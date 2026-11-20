# Life OS — Visión del producto

**Versión:** 0.3 · **Fecha:** 20 de noviembre de 2026

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
| Nota | Contexto y conocimiento | Actual |
| Evento | Cambio relevante | Básico |
| Métrica | Cálculo reproducible | Parcial |

Relación conceptual futura: Área → Objetivo → Proyecto → Hitos/entregables → Tareas. No crear entidades anticipadas sin flujo funcional.

**Distinciones:** actividad no es resultado; tarea completada no implica entregable aceptado; progreso de tareas no equivale a progreso del resultado; finalizar un proyecto es una decisión explícita.

## Módulos
Home (centro diario), Tasks (acciones), Projects (resultados finitos), Habits (consistencia), Notes (conocimiento), Analytics/Reports (evolución), y en el futuro Goals, Work, Business, Finance, AI Orchestrator e Integrations.

## Experiencia central
Home prioriza atención, plan del día, proyectos relevantes, hábitos y captura rápida. Los módulos son espacios de trabajo y permiten acciones contextuales, como crear tareas desde un proyecto. Formularios progresivos, compactos y resilientes. Gráficas solo cuando los datos y la lectura aporten valor.

## Analítica
Tres niveles: estado actual, evolución temporal y resultados. Cada métrica documenta fórmula, fuente, período, zona horaria, faltantes y limitaciones. No inventar datos ni reconstruir historia sin eventos fiables.

## IA y agentes (futuro)
La IA será opcional. Podrá consultar contexto autorizado, analizar, proponer objetivos y planes, mostrar preview y ejecutar solo acciones aprobadas mediante herramientas tipadas. No SQL arbitrario ni permisos irrestrictos. El usuario conserva autoridad.

## Principios
Utilidad primero; jerarquía antes que decoración; fuente de verdad única; propiedad y portabilidad de datos; control humano; local-first; simplicidad técnica; evolución incremental; privacidad por defecto; interoperabilidad futura.

## Dirección técnica
Se mantiene frontend HTML/CSS/JS nativo, FastAPI, SQLAlchemy, SQLite y Alembic en monolito modular local. Esta visión no autoriza frameworks, microservicios, cloud, sync, agentes runtime ni acceso remoto.

## Evolución
0.1 núcleo personal; 0.2 hábitos; Fase 8 consolidación UX; Fase 9 experiencia diaria; Fase 10 modelo de planificación y resultados; Fase 11 Analytics e historial; Fase 12 áreas Work/Business/Finance; Fase 13 AI Orchestrator; Fase 14 integraciones y acceso remoto seguro. Primero experiencia y calidad de datos; después agentes.

## Éxito
El usuario identifica prioridades rápido, captura desde contexto, conecta tareas/proyectos/objetivos sin duplicación, distingue actividad de resultados, entiende métricas y recupera sus datos.

## Fuera de alcance inmediato
Objetivos/áreas/hitos como entidades, Analytics histórico, IA runtime, integraciones, cloud, sync, multiusuario, App Center ejecutable y microservicios.

## Gobierno
La visión orienta; ROADMAP.md y WORK_QUEUE.md autorizan trabajo. Toda entidad, métrica o integración nueva requiere especificación, impacto y aprobación. SECURITY.md prevalece en seguridad.