@echo off
echo =========================================================
echo   AquaVolt-AI Resilient Sync Setup
echo =========================================================
echo This script will register a Windows Task Scheduler job to run 
echo the local resilient sync script every hour at minute 15.
echo.

set "SCRIPT_PATH=%~dp0aquavolt_resilient_sync.py"
set "TASK_NAME=AquaVolt_AI_Sync"

:: Check if python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b
)

echo Registering task "%TASK_NAME%"...
schtasks /create /tn "%TASK_NAME%" /tr "python \"%SCRIPT_PATH%\"" /sc hourly /mo 1 /st 00:15 /f

echo.
if %errorlevel% == 0 (
    echo [SUCCESS] Task created successfully!
    echo Your local PC will now act as a failover server every hour at minute 15.
) else (
    echo [ERROR] Failed to create task. Please try running this script as Administrator.
)
echo.
pause
