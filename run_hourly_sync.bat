@echo off
title AquaVolt-AI: 24/7 Hourly Telemetry Sync Engine
color 0A
cls
echo ===============================================================================
echo   AQUAVOLT-AI: HOURLY MULTI-FARM TELEMETRY SYNC & REPAIR
echo ===============================================================================
echo.
echo [1/3] Running Python Self-Healing Live Sync Engine...
python api\live_farm_sync.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [-] Error executing api\live_farm_sync.py!
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [2/3] Checking Git Status and Adding Updated Data...
git add data\

echo.
echo [3/3] Committing and Pushing to GitHub...
git commit -m "chore(telemetry): manual hourly sync trigger for Pakistan and USA"
git push origin main

echo.
echo ===============================================================================
echo   [OK] HOURLY SYNC COMPLETE & SYNCHRONIZED WITH GITHUB!
echo ===============================================================================
echo.
pause
