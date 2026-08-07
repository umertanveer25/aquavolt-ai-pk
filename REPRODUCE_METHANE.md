# AquaVolt-AI: 8-Year Methane Dataset & Verification Guide

This package contains the 8-year monthly sub-field methane dataset (2019–2026) and the specific scripts required to verify regional methane concentrations and emission proxies.

---

## 📂 Package Contents

* **`data/`**: The complete monthly methane database:
  * `2019/` to `2026/`: 82 monthly sub-field methane files containing:
    * `regional_methane_ppb`: Sentinel-5P TROPOMI column-averaged methane concentrations.
    * `emission_proxy_kg_hr`: Calculated sub-field methane emission rate proxy.
    * `sar_vh_db`: Sentinel-1 SAR C-band backscatter value (used as the high-resolution soil moisture proxy).
    * `confidence_score` & Satellite orbit counts.
* **`aquavolt_gsheet_logger.py`**: The core script containing the physical equations linking Sentinel-5P concentrations with Sentinel-1 SAR moisture proxies.
* **`requirements.txt`**: Python dependencies.

---

## 🔬 Mathematical Methodology

### 1. Sentinel-1 SAR Moisture Proxy
To downscale regional Sentinel-5P measurements ($7\text{km}$ resolution) to $10\text{m}$ sub-field grids, we use the Sentinel-1 SAR C-band backscatter cross-ratio ($\sigma_{vh} / \sigma_{vv}$) as a proxy for surface moisture:
$$\text{RVI} = \frac{4 \cdot \sigma_{vh}}{\sigma_{vv} + \sigma_{vh}}$$
$$\text{NDVI}_{\text{proxy}} = 1.5 \cdot \text{RVI} - 0.1$$

### 2. Methane Emission Proxy ($F_{CH_4}$)
The sub-field emission proxy (kg/hr) is computed by scaling regional column methane against local soil moisture and vegetation proxies:
$$\text{Emission Proxy} = \text{regional\_methane\_ppb} \cdot \left(\text{NDVI}_{\text{proxy}} \cdot \text{SAR\_VH\_db\_ratio}\right) \cdot \text{Scaling Factor}$$

---

## 🛠️ Setup & Run

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the MRV Verification suite to validate the 8-year monthly downscaling and carbon credit calculations:
   ```bash
   python verify_mrv_calculations.py
   ```
3. Run the pipeline to check and log monthly composites:
   ```bash
   python aquavolt_gsheet_logger.py
   ```
