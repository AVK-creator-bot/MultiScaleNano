# MultiscaleNano — one-command local start (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Set-Location $Root
$env:MULTISCALE_ARTIFACT_DIR = Join-Path $Root "data\artifacts"
New-Item -ItemType Directory -Force -Path $env:MULTISCALE_ARTIFACT_DIR | Out-Null

Write-Host "==> MultiscaleNano setup" -ForegroundColor Cyan
Write-Host "    Project root: $Root"

Write-Host "==> Installing Python packages (includes OpenMM)..." -ForegroundColor Cyan
pip install -e "$Root\packages\core" -q
pip install -e "$Root\workers\simulation" -q
pip install -e "$Root\apps\api" -q
pip install openmm -q

Write-Host "==> Installing web dependencies..." -ForegroundColor Cyan
Set-Location "$Root\apps\web"
if (-not (Test-Path "node_modules")) { npm install }

Set-Location $Root

Write-Host ""
Write-Host "==> Starting API on http://localhost:8000" -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root'; `$env:MULTISCALE_ARTIFACT_DIR='$($env:MULTISCALE_ARTIFACT_DIR)'; uvicorn app.main:app --reload --port 8000 --app-dir apps/api"
)

Start-Sleep -Seconds 3

Write-Host "==> Starting Web UI on http://localhost:3000" -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root\apps\web'; npm run dev"
)

Write-Host ""
Write-Host "Ready! Open http://localhost:3000/simulate" -ForegroundColor Green
Write-Host "  1. Click 'Validate structure' on step 1" -ForegroundColor Yellow
Write-Host "  2. Complete the wizard and run OpenMM simulation" -ForegroundColor Yellow
Write-Host ""
Write-Host "Simulations run in-process inside the API (no Redis/worker needed)." -ForegroundColor DarkGray
