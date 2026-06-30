@echo off
title IntelliCoop — Servidor Local
color 0A
cd /d "%~dp0seps_web"

echo.
echo  ==========================================
echo   IntelliCoop — Iniciando servicios...
echo  ==========================================
echo.

:: Verificar que Python este disponible
py --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python no encontrado. Instala Python y agrega al PATH.
    pause
    exit /b 1
)

:: Arrancar Rakkun API (FastAPI) en ventana separada
echo  [1/2] Iniciando Rakkun API en puerto 8001...
start "Rakkun API - FastAPI" cmd /k "cd /d "%~dp0seps_web" && py -m uvicorn rakkun_api:app --port 8001 && pause"

:: Esperar 3 segundos para que FastAPI arranque primero
timeout /t 3 /nobreak >nul

:: Arrancar Django en esta misma ventana
echo  [2/2] Iniciando Django en puerto 8000...
echo.
echo  ==========================================
echo   Abre tu navegador en:
echo   http://localhost:8000
echo  ==========================================
echo.
py manage.py runserver

pause
