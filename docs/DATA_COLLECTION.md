# Data Collection Guide — AquaVolt-AI

## Overview
AquaVolt-AI automatically collects and logs telemetry data every hour via GitHub Actions.
No local machine needs to be running — GitHub's servers handle all data collection.

## Setup in 5 Steps

### Step 1: Fork or Clone this Repository
```bash
git clone https://github.com/umertanveer25/aquavolt-ai-pk.git
cd aquavolt-ai-pk
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Create Google Cloud Service Account
1. Go to https://console.cloud.google.com/
2. Enable **Google Sheets API** and **Google Drive API**
3. Create a Service Account → Download JSON key
4. Create a Google Sheet named: AquaVolt-AI Telemetry Log
5. Share the sheet with your service account email (Editor access)

### Step 4: Add GitHub Secret
In your GitHub repo → Settings → Secrets → Actions:
- Name: GCP_SERVICE_ACCOUNT_KEY
- Value: (paste the full JSON key contents)

### Step 5: Enable GitHub Actions
Go to your repo → Actions tab → Enable workflows

The GitHub Action will now run **every hour** automatically.

---

## Running Locally (Desktop GUI)
```bash
# Install dependencies
pip install -r requirements.txt

# Launch desktop app
python AquaVoltApp.py
```

## Running Local Logger Only
```bash
# Logs to local SQLite (aquavolt_data.db) every hour
python aquavolt_logger.py
```

## Running Google Sheets Logger Manually
```bash
# Set environment variable first
export GCP_SERVICE_ACCOUNT_KEY='{"type":"service_account",...}'
export GSHEET_NAME="AquaVolt-AI Telemetry Log"

python aquavolt_gsheet_logger.py
```

## Data Access

### SQLite (local)
```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('aquavolt_data.db')
df = pd.read_sql('SELECT * FROM telemetry_log ORDER BY timestamp DESC', conn)
print(df.head())
conn.close()
```

### Google Sheets (cloud)
Access your sheet at https://sheets.google.com — data is appended hourly.

---

## Expected Data Volume (Multi-Field 256 Sectors/Hour)
| Timeframe | Records | Size (approx.) |
|---|---|---|
| 1 hour | 256 | ~50 KB |
| 1 day | 6,144 | ~1.2 MB |
| 1 week | 43,008 | ~8.4 MB |
| 1 month | 184,320 | ~36 MB |
| 1 year | 2,242,560 | ~440 MB |

---

## API Endpoints Used

| API / Provider | Endpoint | Purpose |
|---|---|---|
| Open-Meteo | api.open-meteo.com/v1/forecast | Real-time weather, solar rad, soil metrics + ET₀ |
| MS Planetary Computer | planetarycomputer.microsoft.com/api/stac/v1 | STAC query for Sentinel-2 L2A optical scenes |
| MS Planetary Computer | planetarycomputer.microsoft.com/api/stac/v1 | STAC query for MODIS daily LST (Land Surface Temp) |

Both APIs are **free** and require **no registration or API keys**. Credentials for Microsoft Planetary Computer are managed dynamically by the signing library (`planetary_computer`).
