@echo off
setlocal EnableDelayedExpansion
echo ===========================================================================
echo                      NutriMind AI - Development Launcher
echo ===========================================================================
echo.

REM ---------------------------------------------------------------
REM  1. Check Python
REM ---------------------------------------------------------------
echo [CHECK] Python...
where python >nul 2>nul
if errorlevel 1 goto err_nopython
echo        OK

REM ---------------------------------------------------------------
REM  2. Check Node.js + npm
REM ---------------------------------------------------------------
echo [CHECK] Node.js...
where node >nul 2>nul
if errorlevel 1 goto err_nonode
echo        OK

echo [CHECK] npm...
where npm >nul 2>nul
if errorlevel 1 goto err_nonpm
echo        OK

echo.
REM ---------------------------------------------------------------
REM  3. Docker / PostgreSQL
REM ---------------------------------------------------------------
echo [INFO] Checking Docker...
where docker >nul 2>nul
if errorlevel 1 goto no_docker_cli

docker info >nul 2>nul
if errorlevel 1 goto docker_daemon_off

echo        Docker daemon running — starting PostgreSQL...
docker compose -f docker-compose.yml up -d postgres >nul 2>nul
if errorlevel 1 (
    echo [WARN] docker compose up failed. Continuing without Docker PostgreSQL.
) else (
    echo [OK]   PostgreSQL container started.
)
goto docker_done

:docker_daemon_off
echo        Docker daemon not running — using local PostgreSQL if available.
goto docker_done

:no_docker_cli
echo        Docker CLI not found — using local PostgreSQL if available.

:docker_done
echo.

REM ---------------------------------------------------------------
REM  4. Frontend dependencies
REM ---------------------------------------------------------------
echo [CHECK] Frontend node_modules...
if not exist "frontend\node_modules" (
    echo [INFO] node_modules not found. Running npm install...
    pushd frontend
    call npm install
    if errorlevel 1 (
        echo [ERROR] npm install failed. Check the output above.
        popd
        pause
        exit /b 1
    )
    popd
    echo [OK]   npm install complete.
) else (
    echo        OK
)
echo.

REM ---------------------------------------------------------------
REM  5. Launch backend
REM ---------------------------------------------------------------
echo [INFO] Starting backend on port 8000...
if exist "backend\.venv\Scripts\activate.bat" (
    echo        Using virtual environment: backend\.venv
    start "NutriMind Backend" /D "backend" cmd /K "call .venv\Scripts\activate.bat && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
) else (
    echo        No .venv found — using global Python.
    start "NutriMind Backend" /D "backend" cmd /K "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
)

REM ---------------------------------------------------------------
REM  6. Health-check poll
REM ---------------------------------------------------------------
echo [INFO] Waiting for backend to be ready...
set attempt=0

REM Prefer curl (built-in on Windows 10 1803+), fall back to PowerShell
where curl >nul 2>nul
if not errorlevel 1 set USE_CURL=1

:health_loop
set /a attempt+=1

if defined USE_CURL (
    curl -sf --max-time 2 http://127.0.0.1:8000/api/v1/health >nul 2>nul
) else (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try{$r=Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/health' -TimeoutSec 2;exit 0}catch{exit 1}"
)

if not errorlevel 1 goto healthy
if %attempt% geq 40 goto health_timeout

REM Wait ~1 s between polls (ping 127.0.0.1 twice = ~1 s)
ping -n 2 127.0.0.1 >nul
goto health_loop

:healthy
echo [OK]   Backend healthy after %attempt% attempt(s).
echo.
goto start_frontend

:health_timeout
echo [WARN] Backend did not become healthy within ~40 seconds.
echo        The frontend will start anyway — check the Backend window for errors.
echo.

REM ---------------------------------------------------------------
REM  7. Launch frontend
REM ---------------------------------------------------------------
:start_frontend
echo [INFO] Starting frontend (Next.js dev server)...
start "NutriMind Frontend" /D "frontend" cmd /K "npm run dev"

REM ---------------------------------------------------------------
REM  8. Open browser after short delay
REM ---------------------------------------------------------------
echo [INFO] Waiting for frontend to initialise...
ping -n 8 127.0.0.1 >nul
echo [INFO] Opening http://localhost:3000 ...
start "" "http://localhost:3000"

echo.
echo ===========================================================================
echo                   NutriMind AI — Running
echo ===========================================================================
echo.
echo   Backend   :  http://localhost:8000
echo   Frontend  :  http://localhost:3000
echo   API docs  :  http://localhost:8000/docs
echo   Health    :  http://localhost:8000/api/v1/health
echo.
echo   Close the Backend / Frontend windows, or run stop.bat to stop.
echo.
pause
exit /b 0

REM ---------------------------------------------------------------
REM  Error handlers
REM ---------------------------------------------------------------
:err_nopython
echo [ERROR] Python not found in PATH.
echo         Install Python 3.11+ from https://www.python.org/downloads/
pause
exit /b 1

:err_nonode
echo [ERROR] Node.js not found in PATH.
echo         Install Node.js 18+ from https://nodejs.org/
pause
exit /b 1

:err_nonpm
echo [ERROR] npm not found in PATH.
echo         Install Node.js (includes npm) from https://nodejs.org/
pause
exit /b 1
