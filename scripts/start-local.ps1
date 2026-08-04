# MultiscaleNano — one-command local start (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Set-Location $Root
$env:MULTISCALE_ARTIFACT_DIR = Join-Path $Root "data\artifacts"
New-Item -ItemType Directory -Force -Path $env:MULTISCALE_ARTIFACT_DIR | Out-Null

Write-Host "==> MultiscaleNano setup" -ForegroundColor Cyan

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
Write-Host "==> Starting API on http://127.0.0.1:8000" -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root'; `$env:MULTISCALE_ARTIFACT_DIR='$($env:MULTISCALE_ARTIFACT_DIR)'; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000 --app-dir apps/api"
)

Write-Host "==> Waiting for API..." -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    try {
        $h = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health/ready" -TimeoutSec 3 -ErrorAction Stop
        if ($h.simulations_ready) { $ready = $true; break }
    } catch {
        try {
            Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 3 -ErrorAction Stop | Out-Null
        } catch { }
    }
    Start-Sleep -Seconds 2
}

Write-Host "==> Starting Web UI on http://localhost:3000" -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$Root\apps\web'; `$env:API_INTERNAL_URL='http://127.0.0.1:8000'; npm run dev"
)

Write-Host ""
if ($ready) {
    Write-Host "Ready! Open http://localhost:3000/simulate" -ForegroundColor Green
} else {
    Write-Host "Web started — waiting for OpenMM. Open http://localhost:3000/simulate" -ForegroundColor Yellow
}
Write-Host "Keep both terminal windows open while simulating." -ForegroundColor DarkGray
