# IntelliCoop — Arranque local completo
# Doble clic para levantar Django (8000) + Rakkun API (8001)
# Las credenciales se leen del archivo .env (nunca hardcodear aquí)

$dir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# Cargar variables desde .env
$envFile = Join-Path $dir ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]*)\s*=\s*(.*)\s*$') {
            [System.Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), 'Process')
        }
    }
    Write-Host "[.env] Variables cargadas correctamente" -ForegroundColor DarkGray
} else {
    Write-Host "[AVISO] No se encontro .env — asegurate de crearlo desde .env.example" -ForegroundColor Yellow
}

# Rakkun FastAPI en ventana separada
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$dir'; `$env:OPENROUTER_KEY='$env:OPENROUTER_KEY'; `$env:DB_PORT='$env:DB_PORT'; `$env:DB_USER='$env:DB_USER'; `$env:DB_PASS='$env:DB_PASS'; Write-Host '[Rakkun API] Iniciando en http://127.0.0.1:8001' -ForegroundColor Cyan; py -m uvicorn rakkun_api:app --port 8001 --host 127.0.0.1 --reload"
) -WindowStyle Normal

Start-Sleep -Seconds 2

# Django en ventana separada
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$dir'; Write-Host '[Django] Iniciando en http://localhost:8000' -ForegroundColor Green; py manage.py runserver 8000"
) -WindowStyle Normal

Start-Sleep -Seconds 3

# Abrir browser
Start-Process "http://localhost:8000"
Write-Host "IntelliCoop arrancado. Cerrando esta ventana..." -ForegroundColor Yellow
