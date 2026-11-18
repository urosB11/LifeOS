# Preparación de OpenCode — Life OS

**Objetivo:** habilitar OpenCode, Context7 y la skill frontend inicial en el repositorio Life OS sin instalar herramientas innecesarias.

## 1. Requisitos

- Windows 10/11 de 64 bits.
- OpenCode instalado y accesible desde PowerShell (`opencode --version`). La configuración de este repositorio utiliza la clave `plugins` de OpenCode v2.
- Python 3.11 o superior para el desarrollo de Life OS.
- Node.js 22.20 o superior solo para el CLI `skills`; se recomienda instalar Node.js 26.13.1 LTS (versión LTS publicada a la fecha de esta documentación). No instalar una versión Alpha.
- Git disponible desde PowerShell.

El contexto previo indicaba Node 18.16. Esa versión está fuera de soporte y no alcanza el mínimo requerido por el CLI actual de `skills`. Descarga el instalador Windows x64 LTS desde <https://nodejs.org/en/download/>. El proyecto no usa Node para construir ni ejecutar el frontend.

Después de instalar, cierra y vuelve a abrir PowerShell y verifica:

```powershell
node --version
npm --version
npx --version
git --version
python --version
opencode --version
```

Node debe mostrar `v26.13.1` o una versión LTS posterior compatible; en cualquier caso, debe ser como mínimo `v22.20.0`.

## 2. Configuración de Context7

El archivo `opencode.json` registra el plugin de proyecto `@upstash/context7-opencode`. No hace falta instalarlo globalmente ni registrar un MCP duplicado.

1. Abre PowerShell en la raíz de este repositorio.
2. Completa el acceso OAuth de Context7:

```powershell
opencode mcp auth context7
```

3. Completa el flujo en el navegador.
4. Inicia OpenCode con `opencode`. Si ya había una sesión abierta, ciérrala y vuelve a iniciarla para cargar el plugin.

Context7 añade las herramientas de búsqueda documental y la skill `context7-mcp`. La consulta documental necesita Internet, pero no es una dependencia de ejecución de Life OS. Nunca formules preguntas a Context7 que incluyan datos privados del repositorio o del usuario.

## 3. Instalar las skills externas seleccionadas

Ejecuta desde la raíz del proyecto:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup-opencode.ps1
```

El script:

- verifica que Node sea al menos 22.20;
- desactiva telemetría anónima del CLI durante la instalación;
- instala solo `frontend-design` desde `anthropics/skills` y `fastapi` desde el repositorio oficial `fastapi/fastapi`;
- instala la skill para OpenCode, dentro del proyecto, copiando sus archivos en vez de crear symlinks.

No instala el resto de las colecciones ni skills para React/Next.js. `frontend-design` se activa al diseñar o modificar la interfaz; `fastapi` aporta patrones específicos del backend. Las dos son referencias subordinadas a `AGENTS.md`, `REQUIREMENTS.md`, `ARCHITECTURE.md` y `SECURITY.md`.

## 4. Verificar skills

Después de la instalación:

```powershell
npx skills list
```

En el proyecto deben estar disponibles las skills locales:

- `lifeos-feature-workflow`
- `lifeos-data-integrity`
- `lifeos-quality-gate`
- `lifeos-ui-review`

También deben estar disponibles `frontend-design` (Anthropic), `fastapi` (skill oficial del framework) y `context7-mcp` tras instalar/autenticar sus integraciones. OpenCode descubre las skills del proyecto en `.opencode/skills/`.

## 5. Primera apertura

Desde la raíz:

```powershell
opencode
```

En una sesión nueva, utiliza el contenido de `OPENCODE_FIRST_TASK.md` como primer encargo. OpenCode debe revisar documentos y entorno antes de modificar nada, y trabajar únicamente en la Fase 1.

## 6. Actualizaciones de skills

El CLI permite comprobar y actualizar skills instaladas. No actualizar de forma ciega: inspeccionar el diff de los `SKILL.md` actualizados y revisar procedencia y avisos de seguridad antes de aceptar cambios. No instalar colecciones completas por popularidad.

## 7. Decisiones de seguridad

- No pegar secretos, contraseñas ni contenido personal en consultas documentales.
- No permitir que una skill ejecute scripts sin revisar su contenido.
- No cambiar el bind local ni habilitar acceso remoto.
- No conceder permisos globales al agente solo para facilitar la instalación.
- No instalar `webapp-testing` ni `web-design-guidelines` automáticamente en esta etapa: se revisaron y se difirieron por advertencias de auditoría en sus fichas de skills.sh. Se puede reevaluar cuando haya una necesidad concreta.

## 8. Fuentes de las integraciones

- [Anthropic — frontend-design en skills.sh](https://www.skills.sh/anthropics/skills/frontend-design)
- [FastAPI — skill oficial en skills.sh](https://www.skills.sh/fastapi/fastapi/fastapi)
- [Context7 — instrucciones para OpenCode](https://github.com/upstash/context7/blob/master/docs/clients/opencode.mdx)
- [OpenCode — documentación de skills](https://opencode.ai/docs/skills/)
- [skills.sh — CLI y opciones](https://github.com/vercel-labs/skills)
- [Node.js — descargas oficiales](https://nodejs.org/en/download/)

Las auditorías de seguridad de las fichas de `frontend-design` y `fastapi` mostraban Gen Agent Trust Hub, Socket y Snyk en estado Pass al seleccionarlas el 17 de noviembre de 2026. Son controles de terceros y pueden cambiar; revisar de nuevo antes de futuras actualizaciones.
