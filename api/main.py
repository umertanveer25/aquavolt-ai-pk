from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from datetime import datetime, timedelta

app = FastAPI(
    title="AquaVolt-AI Telemetry API",
    description="REST API for programmatic access to AquaVolt-AI agricultural telemetry and water deficit predictions.",
    version="1.0.0"
)

# Allow CORS for web dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
SHEET_ID = '1c2a-3t8fF2g_PX_0ape4ASTsbr5uX0Zb6YPzT8jtuN8'
CSV_URL = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1'

# Security: Define your Premium API Keys here (e.g., from environment variables)
PREMIUM_API_KEYS = {"av_premium_test_key_992"}

def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key not in PREMIUM_API_KEYS:
        raise HTTPException(status_code=401, detail="Unauthorized. Invalid or missing Premium API Key.")
    return x_api_key

def get_data() -> pd.DataFrame:
    """Fetches the live computed telemetry directly from the AquaVolt-AI logger."""
    try:
        df = pd.read_csv(CSV_URL, low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp']).sort_values('timestamp')
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch underlying data: {str(e)}")

@app.get("/")
def root():
    return {"status": "online", "message": "AquaVolt-AI REST API is running. See /docs for endpoints."}

@app.get("/api/v1/telemetry/latest")
def get_latest_telemetry_free():
    """
    FREE TIER: Returns only the last 24 hours of telemetry data.
    Great for live dashboards, trial accounts, or investors.
    """
    df = get_data()
    
    # Filter to last 24 hours only
    cutoff = df['timestamp'].max() - timedelta(hours=24)
    df_filtered = df[df['timestamp'] >= cutoff]
    
    # Replace NaNs with None for JSON serialization
    df_filtered = df_filtered.where(pd.notnull(df_filtered), None)
    
    return {
        "tier": "free",
        "records_returned": len(df_filtered),
        "timestamp_start": cutoff.isoformat(),
        "timestamp_end": df['timestamp'].max().isoformat(),
        "data": df_filtered.to_dict(orient='records')
    }

@app.get("/api/v1/telemetry/history")
def get_historical_telemetry_premium(start_date: str = None, end_date: str = None, api_key: str = Depends(verify_api_key)):
    """
    PREMIUM TIER: Requires 'X-API-Key' header.
    Returns the full historical dataset, optionally filtered by start_date and end_date (YYYY-MM-DD).
    """
    df = get_data()
    
    if start_date:
        df = df[df['timestamp'] >= pd.to_datetime(start_date)]
    if end_date:
        df = df[df['timestamp'] <= pd.to_datetime(end_date)]
        
    df = df.where(pd.notnull(df), None)
    
    return {
        "tier": "premium",
        "records_returned": len(df),
        "data": df.to_dict(orient='records')
    }
