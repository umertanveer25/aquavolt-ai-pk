# 📚 AquaVolt-AI — L2 Operational Scenarios & Memory Wiki

This document maps all high-level operational scenarios and technical improvements executed from inception to the present date.

---

## 🔁 Scenario 1: 24/7 Multi-Farm Ingestion & Self-Healing Engine
* **Context**: Telemetry is gathered hourly across two international hubs (Pakistan & USA).
* **Self-Healing Architecture**:
  * Scans the latest timestamp in CSV files against current UTC time.
  * Detects missing hourly intervals ($\Delta t > 1	ext{ hr}$).
  * Automatically fetches live ERA5 reanalysis and spaceborne indices to backfill gaps.
  * Appends rows conforming strictly to the 23-column `STANDARD_SCHEMA`.
* **Hardened GitHub Actions**:
  * Added automated `git pull --rebase origin main` before pushing in `.github/workflows/hourly_telemetry_sync.yml` to prevent race-condition push rejections.

---

## 🛰️ Scenario 2: Spaceborne Empirical Transition (Zero-Hardware)
* **Context**: Replaced synthetic sine approximations ($\sin(2.1r + 3.4c)$) with true spaceborne observables.
* **Optical**: Microsoft Planetary Computer STAC Sentinel-2 Level-2A BOA reflectance ($ho_{	ext{NIR}}, ho_{	ext{Red}}$).
* **Atmospheric Inversion**: Sentinel-5P TROPOMI column retrievals combined with ERA5 Planetary Boundary Layer Height (PBLH) and wind vectors ($ec{u}$).
* **Hydrology**: C-Band SAR radar backscatter and ERA5 vadose soil moisture $	heta$.

---

## 📄 Scenario 3: Springer Nature LaTeX Manuscript & Overleaf Package
* **Context**: 31-page academic publication under `sn-jnl` class.
* **Figure 1 Overhaul**: Updated with the user's 3-module system architecture infographic + 5 bottom value badges.
* **Float & Layout Rules**: Clean float separation ensuring no two tables or figures stack without explanatory text.
* **Clean Overleaf Package**: Created `AquaVolt_AI_Overleaf_Package.zip` containing `main.tex`, `sn-article.tex`, `sn-bibliography.bib` (45 real DOIs), class files, and 5 high-res 300 DPI figures.

---

## 🛡️ Scenario 4: Wazuh SIEM & Cybersecurity Integration
* **Context**: Enterprise cybersecurity monitoring and tamper detection for dMRV carbon ledgers.
* **File Integrity Monitoring (FIM)**: Real-time tracking of `data/` and `database/` files.
* **FastAPI Middleware**: Streams RFC 5424 JSON logs to `logs/wazuh_security.json`.
* **Custom Detection Rules**: Built `wazuh/rules/aquavolt_rules.xml` covering data manipulation (MITRE T1565.001), sensor spoofing, and API brute-forcing.

---

## 🚁 Scenario 5: UAV Aerial Optical Gas Imaging (FLIR G300a)
* **Context**: High-precision ground-truth calibration for satellite AI models.
* **Payload**: FLIR G300a cooled MWIR optical gas camera detecting in-canopy methane ($	ext{ppm}$) at sub-centimeter resolution.
* **Attestation**: Cryptographically certified with SHA-256 block ledger.
