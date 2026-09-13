@echo off
setlocal EnableExtensions
title TraceACT Launcher - I4C Cybercrime Forensics
color 0B

set "TRACEACT_ROOT=%~dp0"
set "TRACEACT_FRONTEND=%~dp0frontend"
set "TRACEACT_URL=http://localhost:3000"
set "TRACEACT_API_URL=http://127.0.0.1:8001/api/health"

echo.
echo  =======================================================================
echo   TraceACT - Blockchain Intelligence ^& VASP Attribution Workstation
echo   Indian Cyber Crime Coordination Centre ^(I4C^) - SAHYOG Ecosystem
echo  =======================================================================
echo.

cd /d "%TRACEACT_ROOT%"

echo [1/5] Checking runtime dependencies...
if exist "%TRACEACT_ROOT%venv\Scripts\python.exe" (
    set "TRACEACT_PYTHON=%TRACEACT_ROOT%venv\Scripts\python.exe"
    echo [OK] Python: local virtual environment
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] Python was not found. Install Python or create .\venv first.
        goto :failed
    )
    set "TRACEACT_PYTHON=python"
    echo [OK] Python: system installation
)

where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js was not found. Install Node.js 22.13 or newer.
    goto :failed
)
where npm >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm was not found on PATH.
    goto :failed
)
if not exist "%TRACEACT_FRONTEND%\node_modules" (
    echo [ERROR] Frontend dependencies are missing.
    echo         Run: cd frontend ^&^& npm install
    goto :failed
)
echo [OK] Node.js, npm, and frontend packages are available.

echo [2/5] Checking FastAPI on port 8001...
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "try { $response=Invoke-WebRequest -UseBasicParsing -Uri '%TRACEACT_API_URL%' -TimeoutSec 2; if ($response.StatusCode -eq 200) { exit 0 } } catch {}; exit 1"
if errorlevel 1 (
    echo [*] Starting FastAPI backend...
    start "TraceACT Backend API - 8001" /D "%TRACEACT_ROOT%" cmd /k ""%TRACEACT_PYTHON%" -m uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload"
    if errorlevel 1 (
        echo [ERROR] The backend process could not be started.
        goto :failed
    )
) else (
    echo [OK] Reusing the backend already running on port 8001.
)

echo [3/5] Checking investigation console on port 3000...
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "try { $response=Invoke-WebRequest -UseBasicParsing -Uri '%TRACEACT_URL%' -TimeoutSec 2; if ($response.StatusCode -ge 200) { exit 0 } } catch {}; exit 1"
if errorlevel 1 (
    echo [*] Starting investigation console...
    start "TraceACT Investigation Console - 3000" /D "%TRACEACT_FRONTEND%" cmd /k "npm run dev -- --port 3000"
    if errorlevel 1 (
        echo [ERROR] The frontend process could not be started.
        goto :failed
    )
) else (
    echo [OK] Reusing the console already running on port 3000.
)

echo [4/5] Waiting for the investigation console to become ready...
powershell -NoLogo -NoProfile -ExecutionPolicy Bypass -Command "$deadline=(Get-Date).AddSeconds(50); do { try { $response=Invoke-WebRequest -UseBasicParsing -Uri '%TRACEACT_URL%' -TimeoutSec 2; if ($response.StatusCode -ge 200) { exit 0 } } catch {}; Start-Sleep -Milliseconds 750 } while ((Get-Date) -lt $deadline); exit 1"
if errorlevel 1 (
    echo [WARN] The console did not answer within 50 seconds.
    echo        Opening it anyway; review the two service windows for details.
) else (
    echo [OK] Investigation console is ready.
)

echo [5/5] Opening %TRACEACT_URL% ...
start "" "%TRACEACT_URL%"

echo.
echo  =======================================================================
echo   TraceACT services are running:
echo     Investigation console  %TRACEACT_URL%
echo     Backend API docs       http://localhost:8001/docs
echo     Backend health         %TRACEACT_API_URL%
echo  =======================================================================
echo.
echo   You may close this launcher. Keep the two service windows open.
pause >nul
exit /b 0

:failed
echo.
echo  TraceACT could not start. Correct the error above and run start.cmd again.
echo.
pause
exit /b 1
