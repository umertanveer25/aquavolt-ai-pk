import os
import warnings
warnings.filterwarnings('ignore', category=UserWarning, module='matplotlib')
import requests
import json
import math
import random
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Set styling
plt.style.use('dark_background')
sns.set_theme(style="darkgrid", rc={
    "grid.color": "#1e3a5f",
    "grid.linestyle": ":",
    "axes.facecolor": "#1a1a2e",
    "figure.facecolor": "#0e1117",
    "text.color": "white",
    "axes.labelcolor": "#90a4ae",
    "xtick.color": "#90a4ae",
    "ytick.color": "#90a4ae"
})

SHEET_ID = '1c2a-3t8fF2g_PX_0ape4ASTsbr5uX0Zb6YPzT8jtuN8'
url = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Sheet1'

def main():
    print("[INFO] Loading live data from Google Sheet...")
    try:
        df = pd.read_csv(url, low_memory=False)
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df = df.dropna(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
        
        for c in ['air_temp','solar_rad','etc','water_need','humidity','ndvi','kc','ks']:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce')
        
        df['date'] = df['timestamp'].dt.date
        print(f"Loaded {len(df)} rows.")
    except Exception as e:
        print(f"Error loading sheet: {e}")
        return

    # Ensure docs directory exists
    os.makedirs('docs', exist_ok=True)

    # 1. Generate PIML Sigmoid Prior Plot
    generate_piml_plot(df)

    # 2. Generate CIMIS Validation Plots
    generate_baseline_plots(df)

def generate_piml_plot(df):
    print("Generating PIML Sigmoid Prior Plot...")
    try:
        ndvi_range = np.linspace(0, 1, 500)
        kc_prior = 0.15 + 0.95 / (1 + np.exp(-12 * (ndvi_range - 0.4)))
        kc_upper = np.clip(kc_prior + 0.15, 0.15, 1.20)
        kc_lower = np.clip(kc_prior - 0.15, 0.15, 1.20)

        fig, ax = plt.subplots(figsize=(10, 5), facecolor='#0e1117')
        ax.set_facecolor('#1a1a2e')

        ax.fill_between(ndvi_range, kc_lower, kc_upper, alpha=0.15, color='#4fc3f7', label='±0.15 Correction Envelope')
        ax.plot(ndvi_range, kc_prior, color='#4fc3f7', linewidth=2.5, label='Kc Prior (Sigmoid)', zorder=5)
        ax.axhline(0.15, color='#ef5350', linestyle='--', linewidth=1.2, alpha=0.6, label='Min Kc (0.15)')
        ax.axhline(1.20, color='#ef5350', linestyle='--', linewidth=1.2, alpha=0.6, label='Max Kc (1.20)')

        field_colors = {
            'Field-A (Corn)': '#2196F3', 'Field-B (Alfalfa)': '#4CAF50',
            'Field-C (Fallow)': '#FF9800', 'Field-D (Tomato)': '#E91E63'}

        for field, color in field_colors.items():
            if 'field_name' in df.columns:
                fdata = df[df['field_name'] == field]
                if len(fdata) > 0:
                    sample_size = min(150, len(fdata))
                    fdata_sample = fdata.sample(sample_size, random_state=42)
                    ax.scatter(fdata_sample['ndvi'], fdata_sample['kc'], color=color, alpha=0.5, s=12, label=field, zorder=4)

        ax.set_xlabel('NDVI', fontsize=10)
        ax.set_ylabel('Crop Coefficient (Kc)', fontsize=10)
        ax.set_title('Physics-Informed Kc Estimation (Live)', fontsize=12, fontweight='bold', pad=12)
        ax.legend(facecolor='#1a1a2e', labelcolor='white', fontsize=8, loc='upper left')
        ax.tick_params(labelsize=9)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(0, 1.35)
        for sp in ax.spines.values(): sp.set_edgecolor('#1e3a5f')

        plt.tight_layout()
        plt.savefig('docs/piml_sigmoid_prior.png', dpi=120, bbox_inches='tight', facecolor='#0e1117')
        plt.close()
        print("PIML Plot saved.")
    except Exception as e:
        print(f"Failed to generate PIML plot: {e}")

def generate_baseline_plots(df):
    print("Generating Baseline Validation Plots...")
    try:
        # Compute hourly ET0 on the fly
        df['et0'] = df['etc'] / (df['ks'] * df['kc'])
        df['et0'] = df['et0'].replace([np.inf, -np.inf], np.nan).fillna(0.0)

        # First group by timestamp to remove 256x sector duplication for hourly weather
        hourly_weather = df.groupby('timestamp').agg(
            date=('date', 'first'),
            air_temp=('air_temp', 'first'),
            solar_rad=('solar_rad', 'first'),
            humidity=('humidity', 'first'),
            soil_temp=('soil_temp', 'first'),
            precip=('precip', 'first'),
            et0=('et0', 'first')
        ).reset_index()

        # Now aggregate to daily validation parameters
        daily_av = hourly_weather.groupby('date').agg(
            av_temp=('air_temp', 'mean'),
            av_solar=('solar_rad', 'mean'),
            av_humidity=('humidity', 'mean'),
            av_soil_temp=('soil_temp', 'mean'),
            sum_precip=('precip', 'sum'),
            sum_et0=('et0', 'mean')
        ).reset_index()
        daily_av['date'] = pd.to_datetime(daily_av['date'])

        start_date = daily_av['date'].min().strftime('%Y-%m-%d')
        end_date = daily_av['date'].max().strftime('%Y-%m-%d')

        # Fetch real baseline from Open-Meteo (public, no key required)
        baseline_ok = False
        baseline_data_dict = {}
        print("Fetching baseline ground truth observations from Open-Meteo API...")
        try:
            lat, lon = 38.5480, -121.8780
            dt_start = pd.to_datetime(start_date).date()
            dt_today = datetime.utcnow().date()
            past_days = max(1, (dt_today - dt_start).days + 2)
            meteo_url = (
                f"https://api.open-meteo.com/v1/forecast"
                f"?latitude={lat}&longitude={lon}"
                f"&hourly=temperature_2m,shortwave_radiation,relative_humidity_2m,"
                f"soil_temperature_0_to_7cm,precipitation,et0_fao_evapotranspiration"
                f"&past_days={past_days}&forecast_days=0&timezone=UTC"
            )
            mr = requests.get(meteo_url, timeout=20)
            if mr.status_code == 200:
                m_json = mr.json()
                m_hourly = m_json.get("hourly", {})
                m_times = m_hourly.get("time", [])
                m_temps = m_hourly.get("temperature_2m", [])
                m_solar = m_hourly.get("shortwave_radiation", [])
                m_humidity = m_hourly.get("relative_humidity_2m", [])
                m_soil_temp = m_hourly.get("soil_temperature_0_to_7cm", [])
                m_precip = m_hourly.get("precipitation", [])
                m_et0 = m_hourly.get("et0_fao_evapotranspiration", [])

                daily_records = {}
                for i in range(len(m_times)):
                    if m_times[i] is None:
                        continue
                    d_str = m_times[i].split("T")[0]
                    if d_str < start_date or d_str > end_date:
                        continue
                    if d_str not in daily_records:
                        daily_records[d_str] = {
                            "temp": [], "solar": [], "humidity": [],
                            "soil_temp": [], "precip": [], "et0": []
                        }
                    if m_temps[i] is not None: daily_records[d_str]["temp"].append(float(m_temps[i]))
                    if m_solar[i] is not None: daily_records[d_str]["solar"].append(float(m_solar[i]))
                    if m_humidity[i] is not None: daily_records[d_str]["humidity"].append(float(m_humidity[i]))
                    if m_soil_temp[i] is not None: daily_records[d_str]["soil_temp"].append(float(m_soil_temp[i]))
                    if m_precip[i] is not None: daily_records[d_str]["precip"].append(float(m_precip[i]))
                    if m_et0[i] is not None: daily_records[d_str]["et0"].append(float(m_et0[i]))

                for d_str, vals in daily_records.items():
                    if not vals["temp"]:
                        continue
                    baseline_data_dict[d_str] = {
                        'baseline_temp': sum(vals["temp"]) / len(vals["temp"]),
                        'baseline_solar': sum(vals["solar"]) / len(vals["solar"]) if vals["solar"] else 0.0,
                        'baseline_humidity': sum(vals["humidity"]) / len(vals["humidity"]) if vals["humidity"] else 0.0,
                        'baseline_soil_temp': sum(vals["soil_temp"]) / len(vals["soil_temp"]) if vals["soil_temp"] else 0.0,
                        'baseline_precip': sum(vals["precip"]) if vals["precip"] else 0.0,
                        'baseline_et0': sum(vals["et0"]) if vals["et0"] else 0.0
                    }
                baseline_ok = True
        except Exception as e:
            print(f"Open-Meteo fetch failed for plots: {e}")

        # STRICT: No synthetic fallback. If API is down, skip plots entirely.
        if not baseline_ok:
            print("Validation API unavailable. Synthetic generation banned. Skipping baseline plots.")
            return

        baseline_rows = [{'date': pd.to_datetime(k), **v} for k, v in baseline_data_dict.items()]
        baseline_df = pd.DataFrame(baseline_rows)
        merged = pd.merge(daily_av, baseline_df, on='date', how='inner').dropna()

        if len(merged) < 1:
            print("No matching dates for validation plots.")
            return

        # Generate 2x3 scatter plot grid for all 6 variables
        fig, axes = plt.subplots(2, 3, figsize=(18, 10), facecolor='#0e1117')
        axes = axes.flatten()

        pairs = [
            ('baseline_temp', 'av_temp', 'Air Temp (°C)', '#ef5350'),
            ('baseline_solar', 'av_solar', 'Solar Rad (W/m²)', '#ffca28'),
            ('baseline_humidity', 'av_humidity', 'Humidity (%)', '#42a5f5'),
            ('baseline_soil_temp', 'av_soil_temp', 'Soil Temp (°C)', '#ab47bc'),
            ('baseline_precip', 'sum_precip', 'Precipitation (mm)', '#26a69a'),
            ('baseline_et0', 'sum_et0', 'Reference ET0 (mm)', '#26c6da')
        ]

        for i, (baseline_col, av_col, title, color) in enumerate(pairs):
            ax = axes[i]
            ax.set_facecolor('#1a1a2e')
            x = merged[baseline_col]
            y = merged[av_col]
            ax.scatter(x, y, color=color, alpha=0.8, s=40, edgecolor='white', linewidth=0.5)

            r2 = 0.0
            if len(x) > 1 and np.var(x) > 0:
                try:
                    slope, intercept, r, _, _ = stats.linregress(x, y)
                    xline = np.linspace(x.min(), x.max(), 100)
                    ax.plot(xline, slope * xline + intercept, '--', color='white', linewidth=1.2)
                    r2 = r**2
                except Exception:
                    r2 = 0.0
            elif len(x) > 1:
                r2 = 1.0 if np.allclose(x, y) else 0.0
            else:
                r2 = 1.0

            lims = [min(x.min(), y.min()), max(x.max(), y.max())]
            ax.plot(lims, lims, ':', color='#4fc3f7', linewidth=1, alpha=0.5)
            ax.set_xlabel('Open-Meteo Baseline Truth', fontsize=9)
            ax.set_ylabel('AquaVolt-AI Estimate', fontsize=9)
            ax.set_title(f"{title}\nPearson R² = {r2:.3f}", color='white', fontsize=10, fontweight='bold')
            ax.tick_params(labelsize=8)
            for sp in ax.spines.values(): sp.set_edgecolor('#1e3a5f')

        plt.tight_layout()
        plt.savefig('docs/baseline_scatter_validation.png', dpi=120, bbox_inches='tight', facecolor='#0e1117')
        plt.close()
        print("Baseline Validation scatter plot saved.")

    except Exception as e:
        print(f"Failed to generate baseline plots: {e}")

if __name__ == '__main__':
    main()

