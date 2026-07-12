"""
AquaVolt-AI REST API
====================
FastAPI server providing programmatic access to live telemetry,
24-hour LSTM water deficit forecasts, satellite status, and irrigation
recommendations.

Run locally:
    uvicorn api.main:app --reload

Environment variables required:
    AQUAVOLT_PREMIUM_API_KEY  - Secret key for premium tier access
    AQUAVOLT_SHEET_ID         - Google Sheet ID for live telemetry data
"""
import os
import sys
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from datetime import datetime, timedelta

# Allow importing lstm_forecaster and dynamic_registry from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

app = FastAPI(
    title="AquaVolt-AI Telemetry API",
    description=(
        "REST API for programmatic access to AquaVolt-AI agricultural telemetry, "
        "24-hour LSTM water deficit forecasts, and irrigation recommendations.\n\n"
        "**Free tier**: Last 24 hours of telemetry — no key required.\n"
        "**Premium tier**: Full history + forecasting — requires `X-API-Key` header."
    ),
    version="2.0.0",
    contact={
        "name": "Umer Tanveer",
        "email": "umertanveer@awkum.edu.pk",
    },
    license_info={"name": "MIT"},
)

# Allow CORS for web dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Security ─────────────────────────────────────────────────────────────────
# Load from environment variable — NEVER hardcode in source.
# Set via GitHub Secret: AQUAVOLT_PREMIUM_API_KEY
_RAW_KEY = os.environ.get("AQUAVOLT_PREMIUM_API_KEY", "")
PREMIUM_API_KEYS: set[str] = {k.strip() for k in _RAW_KEY.split(",") if k.strip()}


def verify_api_key(x_api_key: str = Header(None)):
    if not PREMIUM_API_KEYS:
        raise HTTPException(
            status_code=503,
            detail="Premium API not configured. Set AQUAVOLT_PREMIUM_API_KEY env var.",
        )
    if not x_api_key or x_api_key not in PREMIUM_API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid or missing Premium API Key.")
    return x_api_key


# ── Data Source ───────────────────────────────────────────────────────────────
SHEET_ID = os.environ.get(
    "AQUAVOLT_SHEET_ID", "1c2a-3t8fF2g_PX_0ape4ASTsbr5uX0Zb6YPzT8jtuN8"
)
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1"


def get_data() -> pd.DataFrame:
    """Fetches the live computed telemetry directly from the AquaVolt-AI Google Sheet."""
    try:
        df = pd.read_csv(CSV_URL, low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check — confirms the API is online."""
    return {
        "status": "online",
        "version": "2.0.0",
        "message": "AquaVolt-AI REST API. See /docs for all endpoints.",
        "satellites_integrated": 19,
        "data_source": "Live Google Sheets telemetry logger",
    }


@app.get("/api/v1/telemetry/latest", tags=["Free Tier"])
def get_latest_telemetry():
    """
    **FREE TIER** — Returns the last 24 hours of telemetry data.
    No API key required. Great for live dashboards and trial access.
    """
    df = get_data()
    cutoff = df["timestamp"].max() - timedelta(hours=24)
    df_filtered = df[df["timestamp"] >= cutoff].where(pd.notnull(df[df["timestamp"] >= cutoff]), None)
    return {
        "tier": "free",
        "records_returned": len(df_filtered),
        "timestamp_start": cutoff.isoformat(),
        "timestamp_end": df["timestamp"].max().isoformat(),
        "data": df_filtered.to_dict(orient="records"),
    }


@app.get("/api/v1/telemetry/history", tags=["Premium Tier"])
def get_historical_telemetry(
    start_date: str = None,
    end_date: str = None,
    api_key: str = Depends(verify_api_key),
):
    """
    **PREMIUM TIER** — Requires `X-API-Key` header.
    Returns full historical dataset, optionally filtered by date range (YYYY-MM-DD).
    """
    df = get_data()
    if start_date:
        df = df[df["timestamp"] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df["timestamp"] <= pd.to_datetime(end_date)]
    df = df.where(pd.notnull(df), None)
    return {
        "tier": "premium",
        "records_returned": len(df),
        "data": df.to_dict(orient="records"),
    }


@app.get("/api/v1/satellites/status", tags=["Free Tier"])
def get_satellite_status():
    """
    **FREE TIER** — Returns the live status of all 19 integrated satellite/sensor plugins.
    Polls each plugin concurrently and returns their current health.
    """
    try:
        import concurrent.futures
        import importlib.util

        plugin_dir = os.path.join(os.path.dirname(__file__), "..", "plugins", "sensors")
        plugin_dir = os.path.abspath(plugin_dir)
        statuses = {}

        def probe_plugin(filepath):
            name = os.path.basename(filepath)[:-3]
            try:
                spec = importlib.util.spec_from_file_location(name, filepath)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                if hasattr(mod, "fetch") and hasattr(mod, "SENSOR_INFO"):
                    result = mod.fetch()
                    return mod.SENSOR_INFO["name"], {
                        "status": result.get("status", "unknown"),
                        "source": result.get("source", "unknown"),
                        "type": mod.SENSOR_INFO.get("type", "unknown"),
                        "resolution": mod.SENSOR_INFO.get("resolution", "unknown"),
                    }
            except Exception as e:
                return name, {"status": "error", "msg": str(e)}
            return name, {"status": "no_sensor_info"}

        files = [
            os.path.join(plugin_dir, f)
            for f in os.listdir(plugin_dir)
            if f.endswith(".py") and not f.startswith("__")
        ]

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(probe_plugin, f) for f in files]
            for future in concurrent.futures.as_completed(futures):
                name, result = future.result()
                if name:
                    statuses[name] = result

        live_count = sum(1 for v in statuses.values() if v.get("status") == "success")
        return {
            "total_plugins": len(statuses),
            "live_count": live_count,
            "failed_count": len(statuses) - live_count,
            "satellites": statuses,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Satellite probe failed: {str(e)}")


@app.get("/api/v1/forecast", tags=["Premium Tier"])
def get_water_deficit_forecast(api_key: str = Depends(verify_api_key)):
    """
    **PREMIUM TIER** — Returns the 24-hour LSTM crop water deficit forecast.
    Trains the neural network on the most recent telemetry history and returns
    an hour-by-hour prediction array in mm.
    """
    try:
        from lstm_forecaster import LSTMForecaster

        forecaster = LSTMForecaster()
        forecaster.train(epochs=3)

        # Use latest telemetry row as seed for the forecast
        df = get_data()
        latest = df.iloc[-1].to_dict() if len(df) > 0 else {}

        seed = {
            "air_temp": float(latest.get("air_temp_c", 28.0) or 28.0),
            "humidity": float(latest.get("humidity_pct", 45.0) or 45.0),
            "solar_rad": float(latest.get("solar_rad_wm2", 600.0) or 600.0),
            "ndvi": float(latest.get("ndvi", 0.70) or 0.70),
            "Kc": float(latest.get("kc", 0.85) or 0.85),
            "Ks": float(latest.get("ks", 0.95) or 0.95),
            "water_need": float(latest.get("water_need_mm", 3.5) or 3.5),
        }

        forecast = forecaster.predict_24h(seed)
        hours = [(datetime.utcnow() + timedelta(hours=i + 1)).strftime("%H:00 UTC") for i in range(24)]

        return {
            "tier": "premium",
            "model": "LSTM (TensorFlow)",
            "seed_timestamp": latest.get("timestamp", "unknown"),
            "forecast_horizon_hours": 24,
            "unit": "mm water deficit",
            "forecast": [{"hour": h, "water_deficit_mm": round(v, 3)} for h, v in zip(hours, forecast)],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")


@app.get("/api/v1/fields/{field_id}/recommendation", tags=["Premium Tier"])
def get_field_recommendation(field_id: str, api_key: str = Depends(verify_api_key)):
    """
    **PREMIUM TIER** — Returns a direct irrigation recommendation in mm for a specific field.
    field_id examples: 'Field-A', 'Field-B', 'Field-C', 'Field-D'
    """
    valid_fields = ["Field-A", "Field-B", "Field-C", "Field-D"]
    if field_id not in valid_fields:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown field '{field_id}'. Valid fields: {valid_fields}",
        )

    df = get_data()
    if len(df) == 0:
        raise HTTPException(status_code=503, detail="No telemetry data available.")

    # Filter for the requested field if column exists
    if "field" in df.columns:
        field_df = df[df["field"].str.contains(field_id, case=False, na=False)]
    else:
        field_df = df

    latest = field_df.iloc[-1].to_dict() if len(field_df) > 0 else df.iloc[-1].to_dict()

    water_need = float(latest.get("water_need_mm", 0.0) or 0.0)
    et0 = float(latest.get("et0_mm_day", 0.0) or 0.0)
    kc = float(latest.get("kc", 0.85) or 0.85)
    ks = float(latest.get("ks", 1.0) or 1.0)

    # Irrigation recommendation: apply water if deficit > 5mm threshold
    recommend_irrigation = water_need > 5.0
    urgency = "HIGH" if water_need > 15.0 else ("MEDIUM" if water_need > 5.0 else "LOW")

    return {
        "field_id": field_id,
        "timestamp": str(latest.get("timestamp", "unknown")),
        "current_water_deficit_mm": round(water_need, 2),
        "et0_mm_day": round(et0, 2),
        "crop_coefficient_kc": round(kc, 3),
        "stress_coefficient_ks": round(ks, 3),
        "recommend_irrigation": recommend_irrigation,
        "recommended_irrigation_mm": round(water_need, 1) if recommend_irrigation else 0.0,
        "urgency": urgency,
        "note": "Apply recommended volume at next scheduled irrigation window.",
    }
