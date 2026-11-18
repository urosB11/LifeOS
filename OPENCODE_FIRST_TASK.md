# Primer encargo para OpenCode — Life OS / Fase 1

Copia y pega el siguiente mensaje en OpenCode desde la raíz del repositorio:

---

Vamos a iniciar Life OS. Lee `AGENTS.md` y todos los documentos que ese archivo indica antes de modificar código.

**Autorización actual: implementar exclusivamente la Fase 1 de `ROADMAP.md` — Fundaciones ejecutables.** No avances a CRUD de tareas/proyectos/notas ni a otras fases.

Primero inspecciona el estado completo del directorio y del repositorio (`git status`, archivos existentes, versiones de Python, Git y OpenCode). No sobrescribas ni elimines archivos o cambios previos. Comprueba también la configuración de Context7 y las skills disponibles (`lifeos-*`, `frontend-design`, `fastapi` y `context7-mcp`). Si el plugin o la skill frontend no están instalados, informa el estado y sigue solo con las tareas que no dependan de ellos.

Prepara un plan pequeño que cubra únicamente:

1. estructura inicial mínima del repositorio;
2. entorno Python y dependencias definidas en `ARCHITECTURE.md`;
3. FastAPI/Uvicorn escuchando solo en `127.0.0.1:8000`;
4. frontend estático mínimo servido por FastAPI en el mismo origen;
5. endpoint `/api/v1/health`;
6. base SQLite de desarrollo vacía, configuración SQLAlchemy/Alembic y claves foráneas activadas;
7. pytest/HTTPX y Ruff;
8. `.gitignore` que excluya datos, backups, bases reales, secretos y entornos virtuales;
9. README con pasos reproducibles de instalación, ejecución y pruebas.

No agregues framework frontend, bundler, Docker, CORS abierto, autenticación, telemetría, IA, plugins de aplicación ni servicios externos. No uses la base personal para pruebas. No expongas el servidor a LAN o Internet.

Antes de implementar, presenta el plan y señala cualquier conflicto real que encuentres entre los documentos y el estado del repositorio. Si no hay bloqueos, implementa en incrementos pequeños, ejecuta las pruebas y revisa el diff. No hagas push ni publiques. Al finalizar informa exactamente qué cambió, qué comandos ejecutaste, resultados de tests, limitaciones y próximos pasos. No afirmes que algo está verificado si no lo ejecutaste.

---
