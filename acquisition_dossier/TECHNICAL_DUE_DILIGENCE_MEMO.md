# 🔬 AquaVolt-AI — Technical Due Diligence Memorandum
### Prepared for Technical Evaluation Committees & M&A Teams

---

### 1. Codebase Architecture & Modularity
* **Repository**: `https://github.com/umertanveer25/aquavolt-ai-pk.git` (Active `main` branch).
* **Languages & Stack**: Python 3.11, FastAPI, Pandas, NumPy, SciPy, Microsoft Planetary Computer STAC, Open-Meteo ERA5, LaTeX (`sn-jnl`).
* **Containerization**: Docker Compose (`docker-compose.yml` & `wazuh/docker-compose.wazuh.yml`).

---

### 2. Dataset Assets & Provenance
* **Total Stored Telemetry**: **2,192,238 rows** across 12 CSV files.
* **Longitudinal Series**: 2019 to August 2026 (Continuous 8-Year decadal time series).
* **Field Sites**:
  * Pakistan Rice Hub ($32.0886^\circ	ext{ N}, 73.5914^\circ	ext{ E}$): 284,334 live rows.
  * USA Russell Ranch ($38.5480^\circ	ext{ N}, -121.8790^\circ	ext{ W}$): 535,423 live rows.
* **UAV Calibration**: FLIR G300a mid-wave infrared gas camera flight certified with SHA-256 hash `72bdc883...122e`.

---

### 3. Cybersecurity & Data Integrity (Wazuh SIEM / XDR)
* **File Integrity Monitoring (FIM)**: Real-time hash monitoring on `data/`, `database/`, and `api/`.
* **SIEM Rules**: Custom XML rules (`wazuh/rules/aquavolt_rules.xml`) detecting MITRE `T1565.001` Data Manipulation, sensor spoofing ($F_{\mathrm{CH}_4} > 50	ext{ kg/hr}$), and API brute force.
* **Audit Logging**: 10MB rotating RFC 5424 structured JSON stream (`logs/wazuh_security.json`).

---

### 4. Academic Publication & IP Transfer
* **Manuscript**: 31-page manuscript prepared for Springer Nature.
* **Bibliography**: 45 real peer-reviewed papers with verified active DOIs.
* **Deliverable**: Ready-to-compile Overleaf bundle (`AquaVolt_AI_Overleaf_Package.zip`).
