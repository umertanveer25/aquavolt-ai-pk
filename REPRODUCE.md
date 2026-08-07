# AquaVolt-AI: 8-Year Methane & Evapotranspiration dMRV Reproducibility Guide

This package contains the complete dataset, source code, physics-informed model weights, and scripts required to reproduce the 8-year sub-field methane, evapotranspiration ($ET_c$), and carbon credit calculations for the UC Davis Russell Ranch Sustainable Agriculture Facility.

---

## 📂 Package Contents

* **`data/`**: The complete telemetry and carbon accounting database:
  * `2019/` to `2026/`: 82 monthly sub-field methane composite files containing regional concentrations (ppb), computed emission proxies (kg/hr), and Sentinel-1 SAR backscatter value logs.
  * `telemetry_log_2026_06_to_08.csv`: The hourly, high-frequency 154,367 record dataset.
  * `carbon_credit_report.csv`: Summary of carbon credits generated per field based on water conservation.
  * `PROVENANCE.json`: Cryptographic audit ledger verifying data source integrity.
* **`ai_weights_mlp.json`**: Trained model weights for the Physics-Informed Machine Learning (PIML) residual crop stress calculator.
* **`aquavolt_gsheet_logger.py`**: The core telemetry sync, physical correction (FAO-56), and PIML model runner.
* **`generate_plots.py`**: Visual verification script generating correlation and telemetry timeseries charts.
* **`lstm_forecaster.py`**: Autoregressive LSTM 24-step forecasting model.
* **`requirements.txt`**: Python dependencies.

---

## 🛠️ Step-by-Step Setup & Reproduction

### 1. Install Dependencies
Ensure you have Python 3.10+ installed. Open a terminal in this directory and run:
```bash
pip install -r requirements.txt
```

### 2. Run Telemetry Data Ingestion & PIML
You can execute the core pipeline to pull satellite updates and compute crop water stress ($K_s$) and evapotranspiration locally:
```bash
python aquavolt_gsheet_logger.py
```
*Note: If you do not have Google Sheets API credentials, the script will automatically fallback to local CSV storage and write to `data/telemetry_log_2026_06_to_08.csv`.*

### 3. Generate Verification Figures & Charts
To regenerate the verification and correlation charts:
```bash
python generate_plots.py
```
This will recreate the timeseries and scatter plots inside the `docs/` folder.

### 4. Run Autoregressive Water Deficit Forecasts
To run the LSTM forecaster and predict water deficit for the next 24 hours:
```bash
python lstm_forecaster.py
```

### 5. Run Verification Unit Tests
To verify physical limit compliance and model correctness:
```bash
pytest tests/
```
