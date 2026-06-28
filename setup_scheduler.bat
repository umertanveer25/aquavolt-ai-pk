@echo off
echo =========================================================
echo   AquaVolt-AI Resilient Sync Setup
echo =========================================================
echo This script will register a Windows Task Scheduler job to run 
echo the local resilient sync script every hour at minute 00.
echo The script downloads data immediately, then waits until minute 15
echo to check if GitHub succeeded. If not, it pushes the data itself.
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
schtasks /create /tn "%TASK_NAME%" /tr "python \"%SCRIPT_PATH%\"" /sc hourly /mo 1 /st 00:00 /f
powershell -Command "Set-ScheduledTask -TaskName '%TASK_NAME%' -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries)"

echo.
if %errorlevel% == 0 (
    echo [SUCCESS] Task created successfully!
    echo Your local PC will now:
    echo   1. Download and process data at the exact hour mark
    echo   2. Hold data in memory until minute 15
    echo   3. If GitHub pushed data, discard local copy
    echo   4. If GitHub failed, push local data to Google Sheets
    echo   5. Save a local backup and clean up files older than 3 hours
) else (
    echo [ERROR] Failed to create task. Please try running this script as Administrator.
)
echo.
pause
