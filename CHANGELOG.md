# Changelog

All notable changes to AquaVolt-AI are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [2.1.0] – 2026-07-12

### Added
- `lstm_forecaster.py` — 24-hour LSTM crop water deficit forecasting engine with TensorFlow/Keras, autoregressive sliding-window inference, and analytical physics-based fallback.
- `api/main.py` — 3 new REST endpoints: `GET /api/v1/forecast`, `GET /api/v1/satellites/status`, `GET /api/v1/fields/{field_id}/recommendation`.
- `requirements-dev.txt` — Separated heavy dev dependencies (TensorFlow, PySide6, matplotlib) from the lightweight production `requirements.txt`.
- `tests/test_aquavolt.py` — Added `TestLSTMForecaster` (5 tests) and `TestPluginRegistry` (5 tests) for full CI coverage.
- `.github/workflows/hourly_sync.yml` — Added separate `test` job that runs `pytest` automatically on every push and pull request.
- `Dockerfile` + `docker-compose.yml` — One-command Docker deployment for the FastAPI REST server.
- `CHANGELOG.md` — This file.

### Fixed
- Removed 5 duplicate sensor plugin files: `ecostress.py`, `nasa_gpm_imerg.py`, `nasa_modis_mcd43.py`, `cimis_stations.py`, `nasa_ecostress_70m.py`. These caused double-registration in the dynamic plugin registry.
- Removed hardcoded `PREMIUM_API_KEYS` from `api/main.py`. Now loaded exclusively from `AQUAVOLT_PREMIUM_API_KEY` environment variable.
- Added `httpx>=0.25.0` and `aiohttp>=3.9.0` to `requirements.txt` (required by FastAPI async clients but were missing).
- GitHub Actions now passes `AQUAVOLT_PREMIUM_API_KEY` and `AQUAVOLT_SHEET_ID` via GitHub Secrets instead of hardcoding.

### Security
- `service_account.json` confirmed to be in `.gitignore` — credentials are never committed to the repository.

---

## [2.0.0] – 2026-07-01

### Added
- 19-satellite live plugin architecture with auto-discovery registry (`dynamic_registry.py`).
- All 19 sensor plugins converted from mocked/simulated data to live REST API calls.
- NASA VIIRS SNPP (375m) via NASA CMR STAC LANCEMODIS + LPCLOUD dual-provider fallback.
- OpenLandMap via GeoServer WMS GetFeatureInfo (bypasses broken REST endpoint).
- NASA POWER queried 5 days back to avoid processing lag and `-999` fill values.
- CIMIS ground station proxied through Open-Meteo hourly ground archive.
- Resilient ensemble fusion with `ThreadPoolExecutor` concurrent ingestion.
- AI sensor weight gradient descent system (`ai_weights.json`).
- FastAPI REST server (`api/main.py`) with Free and Premium tier endpoints.
- Streamlit web dashboard (`streamlit_app.py`).

### Changed
- Satellite ensemble now covers: NASA POWER, Open-Meteo, SMAP, GPM IMERG, ECOSTRESS, GOES-16, MODIS MOD11A1, MODIS MCD43A4, Landsat 8/9, Sentinel-1, Sentinel-2, Sentinel-3, ERA5-Land, CHIRPS, SoilGrids, OpenLandMap, VIIRS, PlanetScope, CIMIS.

---

## [1.0.0] – 2026-06-15

### Added
- Initial AquaVolt-AI system with FAO-56 Penman-Monteith ET₀ calculation.
- Physics-Informed Machine Learning (PIML) sigmoid prior for crop coefficient Kc.
- Google Sheets telemetry logger (`aquavolt_gsheet_logger.py`).
- PySide6 desktop dashboard (`AquaVoltApp.py`).
- GitHub Actions hourly cron sync.
- 8×8 spatial NDVI crop health grid (64 sectors per field, 4 fields, 256 rows/hour).
- Unit tests for physics engine and statistical validation (`tests/test_aquavolt.py`).
