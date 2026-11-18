$ErrorActionPreference = "Stop"

function Stop-WithMessage([string]$Message) {
    Write-Error $Message
    exit 1
}

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCommand) {
    Stop-WithMessage "Node.js no está instalado o no está en PATH. Instala Node.js 26 LTS desde https://nodejs.org/en/download/ y vuelve a abrir PowerShell."
}

$nodeVersionText = (& node --version).Trim()
$versionMatch = [regex]::Match($nodeVersionText, '^v?(\d+)\.(\d+)\.(\d+)')
if ($LASTEXITCODE -ne 0 -or -not $versionMatch.Success) {
    Stop-WithMessage "No se pudo determinar la versión de Node.js."
}

$major = [int]$versionMatch.Groups[1].Value
$minor = [int]$versionMatch.Groups[2].Value
if (($major -lt 22) -or (($major -eq 22) -and ($minor -lt 20))) {
    Stop-WithMessage "Node.js $nodeVersionText no alcanza el mínimo 22.20. Instala una versión LTS actual (recomendado Node 26 LTS) y vuelve a abrir PowerShell."
}

$npxCommand = Get-Command npx -ErrorAction SilentlyContinue
if (-not $npxCommand) {
    Stop-WithMessage "No se encuentra npx en PATH. Reinstala Node.js LTS y vuelve a abrir PowerShell."
}

$opencodeCommand = Get-Command opencode -ErrorAction SilentlyContinue
if (-not $opencodeCommand) {
    Stop-WithMessage "No se encuentra OpenCode en PATH. Instala o repara OpenCode antes de continuar."
}

Write-Host "Node.js detectado: $nodeVersionText"
Write-Host "Instalando las skills frontend-design (Anthropic) y fastapi (oficial) para OpenCode..."

# Opt out of the skills CLI's anonymous install telemetry for this process.
$env:DISABLE_TELEMETRY = "1"

& npx --yes skills add anthropics/skills --skill frontend-design --agent opencode --copy --yes
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Falló la instalación de frontend-design. Revisa la conexión y el mensaje anterior; no se modificó la configuración global de OpenCode."
}

& npx --yes skills add https://github.com/fastapi/fastapi --skill fastapi --agent opencode --copy --yes
if ($LASTEXITCODE -ne 0) {
    Stop-WithMessage "Falló la instalación de la skill oficial de FastAPI. frontend-design puede haber quedado instalada; revisa el listado antes de reintentar."
}

Write-Host "Skills instaladas. Skills visibles para el CLI:"
& npx --yes skills list
if ($LASTEXITCODE -ne 0) {
    Write-Warning "La instalación terminó, pero no se pudo listar las skills. Verifica en .opencode/skills."
}

Write-Host "Listo. Ahora autentica Context7 con: opencode mcp auth context7 y luego inicia OpenCode con: opencode"
