@echo off
echo =========================================================
echo   AquaVolt-AI Resilient Sync Setup
echo =========================================================
echo This script will register a Windows Task Scheduler job to run 
echo the local resilient sync script every hour at minute 00.
echo The script downloads data immediately, then waits until minute 15
echo to check if GitHub succeeded. If not, it pushes the data itself.
echo.

set "SCRIPT_PATH=%~dp0resilient_sync.bat"
set "TASK_NAME=AquaVolt-ResilientSync"

echo Registering task: %TASK_NAME%
schtasks /create /tn "%TASK_NAME%" /tr "%SCRIPT_PATH%" /sc hourly /st 00:00 /f

echo.
echo Task registered successfully.
echo.
pause
