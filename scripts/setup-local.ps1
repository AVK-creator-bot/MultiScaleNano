# One-time MultiscaleNano setup (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "==> MultiscaleNano one-time setup" -ForegroundColor Cyan
Write-Host "    Project root: $Root"

Write-Host "==> Installing Python packages + OpenMM..." -ForegroundColor Cyan
pip install -e "$Root\packages\core" -q
pip install -e "$Root\workers\simulation" -q
pip install -e "$Root\apps\api" -q
pip install openmm -q

Write-Host "==> Installing web dependencies..." -ForegroundColor Cyan
Set-Location "$Root\apps\web"
npm install

Write-Host ""
Write-Host "Setup complete. Start the app with:" -ForegroundColor Green
Write-Host "  .\scripts\start-local.ps1" -ForegroundColor White
Write-Host ""
Write-Host "Or manually:" -ForegroundColor DarkGray
Write-Host "  Terminal 1: cd $Root; `$env:MULTISCALE_ARTIFACT_DIR='$Root\data\artifacts'; uvicorn app.main:app --port 8000 --app-dir apps/api"
Write-Host "  Terminal 2: cd $Root\apps\web; npm run dev"
