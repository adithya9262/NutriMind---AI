@echo off
setlocal

echo ===========================================================================
echo                      NutriMind AI - Development Stopper
echo ===========================================================================
echo.

REM ---------------------------------------------------------------------------
REM  Close backend window
REM ---------------------------------------------------------------------------

echo [INFO] Closing NutriMind Backend window...
taskkill /FI "WINDOWTITLE eq NutriMind Backend*" /T >nul 2>nul
if errorlevel 1 (
    echo        Backend window not found or already closed.
) else (
    echo [OK]   Backend closed.
)

REM ---------------------------------------------------------------------------
REM  Close frontend window
REM ---------------------------------------------------------------------------

echo [INFO] Closing NutriMind Frontend window...
taskkill /FI "WINDOWTITLE eq NutriMind Frontend*" /T >nul 2>nul
if errorlevel 1 (
    echo        Frontend window not found or already closed.
) else (
    echo [OK]   Frontend closed.
)

echo.

REM ---------------------------------------------------------------------------
REM  Docker PostgreSQL cleanup (only if Docker is running)
REM ---------------------------------------------------------------------------

echo [INFO] Checking Docker for PostgreSQL cleanup...
where docker >nul 2>nul
if errorlevel 1 (
    echo        Docker CLI not found -- skipping.
) else (
    docker info >nul 2>nul
    if errorlevel 1 (
        echo        Docker daemon not running -- skipping.
    ) else (
        echo        Stopping PostgreSQL via Docker Compose...
        docker compose down
        if errorlevel 1 (
            echo [WARN] docker compose down had issues.
        ) else (
            echo [OK]   PostgreSQL stopped.
        )
    )
)

echo.
echo ===========================================================================
echo                      NutriMind AI Stopped
echo ===========================================================================
echo.
pause
