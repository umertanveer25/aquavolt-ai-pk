# AquaVolt-AI 🌿💧

**Physics-Informed Satellite-Driven Crop Water-Energy Optimization System**

Developed by **Umer Tanveer**, PhD Candidate, Department of Computer Science, Abdul Wali Khan University Mardan (AWKUM), Pakistan.

---

## Overview

AquaVolt-AI combines:
- 🛰️ NASA MODIS NDVI (open access, no API key)
- 🌤️ Open-Meteo Real-Time Weather API
- 🔬 Physics-Informed Machine Learning (PIML) — FAO-56 Penman-Monteith ET0
- ☀️ Dynamic Crop Growth Engine (astronomical solar declination + temperature curve)
- 🗄️ SQLite local database + Google Sheets cloud logging

## Files

| File | Description |
|---|---|
| AquaVoltApp.py | Main desktop GUI (PySide6) |
| aquavolt_logger.py | Local hourly logger to SQLite |
| aquavolt_gsheet_logger.py | Hourly Google Sheets cloud logger |
| .github/workflows/hourly_sync.yml | GitHub Action — hourly auto-sync |

## Location
AWKUM Research Farm, Mardan, Pakistan (34.1975 N, 72.0168 E)

## Citation
Tanveer, U. (2026). AquaVolt-AI: Physics-Informed Satellite-Driven Crop Water-Energy Optimization. AWKUM, Pakistan.
