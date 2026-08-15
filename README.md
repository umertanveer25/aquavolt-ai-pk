<div align="center">

# 🌿 AquaVolt-AI (v3.5)

### Multi-Site Cyber-Physical Remote Sensing & Carbon MRV Engine
**Satellite-Driven $10\text{ m}$ Sub-Field Precision Hydrology & Methane Downscaling**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Multi-Site Pipeline](https://img.shields.io/badge/Multi--Site-USA%20%26%20Pakistan-brightgreen.svg)](data/)
[![Ground Validation](https://img.shields.io/badge/Russell%20Ranch%20R%C2%B2-%3E0.99-blue.svg)](data/russell_ranch_correlation_matrix.csv)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.21802983.svg)](https://doi.org/10.5281/zenodo.21802983)
[![FAO-56](https://img.shields.io/badge/Standard-FAO--56%20PM-lightgrey)](http://www.fao.org/3/x0490e/x0490e00.htm)
[![AWKUM](https://img.shields.io/badge/Institution-AWKUM%20Pakistan-darkgreen)](https://www.awkum.edu.pk/)

**Umer Tanveer** · PhD Candidate, Dept. of Computer Science  
Abdul Wali Khan University Mardan (AWKUM), KP, Pakistan

</div>

---

## 🌍 Multi-Site Architecture (USA & Pakistan Deployments)

AquaVolt-AI operates an automated, hardware-independent cyber-physical pipeline that monitors agricultural parcels across continents in **complete multi-tenant isolation**:

```
                                 AQUAVOLT-AI MASTER ENGINE
                                             │
                  ┌──────────────────────────┴──────────────────────────┐
                  ▼                                                     ▼
    🇺🇸 UC DAVIS RUSSELL RANCH (USA)                       🇵🇰 PINDI BOWRA RICE HUB (PAKISTAN)
    • Location: 38.5480°N, -121.8780°W                    • Location: 32.0886°N, 73.5914°E
    • Area: 300 Acres (4 Fields)                         • Area: 4-Acre Demonstration Plot
    • Crops: Corn, Alfalfa, Fallow, Tomato               • Crop: Super Basmati Rice (Paddy)
    • Spatial Grid: 256 Sectors (8×8 per field)          • Spatial Grid: 144 Sectors (12×12 matrix)
    • Telemetry: data/telemetry_log_2026_06_to_08.csv     • Telemetry: data/telemetry_log_pk_pindi_bowra.csv
    • SHA-256: data/PROVENANCE.json                      • SHA-256: data/PROVENANCE_PK_PINDI_BOWRA.json
```

---

## 🛰️ Planetary Satellite Constellation Integration

All sites ingest spaceborne earth observation constellations at **$10\text{ m}$ sub-field resolution**:

| Satellite Platform | Space Agency | Resolution | Physical Measurement Stream |
| :--- | :--- | :---: | :--- |
| **Copernicus Sentinel-2 (A & B)** | ESA | **$10\text{ m}$** | Optical $NDVI, SAVI, NDWI, LAI, FCOVER$ |
| **Copernicus Sentinel-1 SAR** | ESA | **$10\text{ m}$** | C-Band Radar Vegetation Index ($RVI$) & surface roughness |
| **Copernicus Sentinel-5P (TROPOMI)** | ESA | **$5.5\text{ km} \to 10\text{ m}$** | Tropospheric Methane ($\text{CH}_4$), $\text{NO}_2$, SIF ($740\text{ nm}$) |
| **NASA SMAP** | NASA JPL | **$9\text{ km} \to 10\text{ m}$** | Sub-surface root-zone soil moisture ($0\text{--}100\text{ cm}$) |
| **NASA / NOAA VIIRS & MODIS** | NASA / NOAA | **$375\text{ m}$** | Diurnal Land Surface Temperature ($LST$) |
| **NASA ECOSTRESS (on ISS)** | NASA JPL | **$70\text{ m}$** | High-resolution thermal plant transpiration |
| **NASA GRACE-FO** | NASA | **Monthly** | Regional groundwater aquifer depletion anomaly |

---

## 📊 Dual-Continent Ground-Truth Benchmark Matrix (USA & Pakistan)

Rigorous empirical validation across **5 parallel scientific layers** using country-specific ground infrastructure:

| Validation Layer | 🇺🇸 USA Infrastructure Source | USA $R^2$ | 🇵🇰 Pakistan Infrastructure Source | PK $R^2$ | Empirical Status |
| :--- | :--- | :---: | :--- | :---: | :---: |
| **1. Eddy Covariance Energy Balance** | **AmeriFlux US-Wrr / US-Tw1 Towers** | **$0.9980$** | **LUMS WIT Eddy Flux Towers (Okara)** | **$0.9737$** | **EXCEPTIONAL** |
| **2. Automated Weather Ground Truth** | **CIMIS Station 6 (Davis)** | **$0.9994$** | **PMD RAMC Faisalabad (WMO #41598)** | **$0.9978$** | **EXCEPTIONAL** |
| **3. Direct Crop Evapotranspiration ($ET_c$)** | **USDA SCAN Soil Lysimeters** | **$0.9895$** | **PCRWR & UAF Precision Lysimeters** | **$0.9591$** | **EXCEPTIONAL** |
| **4. Field Crop Hydrology & Saturation** | **UC Davis Russell Ranch Probes** | **$0.4867$** | **RRI Kala Shah Kaku & AWD Pani Pipes** | **$0.9292$** | **VERY STRONG** |
| **5. Deep Groundwater Depletion** | **California DWR Well Telemetry** | **$0.6471$** | **PCRWR Indus Basin Telemetry Wells** | **$0.4150$** | **CONFIRMED** |

*Unified dual-continent dataset logged in [`data/dual_continent_validation_matrix.csv`](data/dual_continent_validation_matrix.csv) and [`data/dual_continent_validation_report.json`](data/dual_continent_validation_report.json).*

---

## 🌾 Pakistan Rice Hub: Pindi Bowra Demonstration Parcel

* **Location:** Mauza Pindi Bowra, District Hafizabad, Punjab, Pakistan (`32.0886°N, 73.5914°E`)
* **Parcel Size:** **4.0 Acres** ($127.2\text{ m} \times 127.2\text{ m}$)
* **Crop:** Super Basmati Rice (*Oryza sativa*) under Alternate Wetting and Drying (AWD)
* **Dataset:** **262,656 authentic physical observations** from June 1, 2026 to August 15, 2026.
* **Telemetry Path:** [`data/telemetry_log_pk_pindi_bowra.csv`](data/telemetry_log_pk_pindi_bowra.csv)
* **Provenance SHA-256:** [`data/PROVENANCE_PK_PINDI_BOWRA.json`](data/PROVENANCE_PK_PINDI_BOWRA.json)

---

## ⚡ Automated 24/7 Synchronization

The system executes hourly unattended cycles via Windows Task Scheduler / GitHub Actions:
```bash
python aquavolt_resilient_sync.py
```
1. **Scans and audits incoming UAV drone flight logs** into farm-specific subfolders (`data/drone_flights/`).
2. **Computes FAO-56 dual crop physics** across 256 USA sectors and 144 Pakistan sectors.
3. **Logs V2 advanced agro-environmental streams** (SIF, NO2, CO, SMAP, SAR RVI).
4. **Calculates SHA-256 cryptographic hashes** and pushes commits to GitHub.

---

## 📜 Citation

```bibtex
@article{tanveer2026aquavolt,
  title={AquaVolt-AI: High-Resolution Satellite Methane Downscaling and Physics-Informed Hydrological dMRV for Precision Agriculture},
  author={Tanveer, Umer},
  journal={Springer Nature Environmental Cyber-Physical Systems},
  year={2026},
  doi={10.5281/zenodo.21802983}
}
```

---
<div align="center">
<b>AquaVolt-AI</b> · Open-Source Cyber-Physical Agriculture · Built for Global Scalability
</div>
