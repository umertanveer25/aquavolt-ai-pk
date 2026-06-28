import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

# ── Page Config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AquaVolt-AI | Live Telemetry",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Custom CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .main-header {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        padding: 2rem;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 2rem;
        border: 1px solid #1e3a5f;
    }
    .main-header h1 { color: #ffffff; font-size: 2.2rem; margin: 0; font-weight: 700; }
    .main-header p  { color: #90caf9; font-size: 1rem; margin: 0.5rem 0 0 0; }
    
    .metric-card {
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border: 1px solid #0f3460;
        border-radius: 12px;
        padding: 1.2rem;
        text-align: center;
    }
    .metric-card .value { font-size: 2rem; font-weight: 700; color: #4fc3f7; }
    .metric-card .label { font-size: 0.85rem; color: #90a4ae; margin-top: 0.2rem; }
    
    .field-tag {
        display: inline-block;
        padding: 0.2rem 0.7rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .stTabs [data-baseweb="tab"] { font-size: 1rem; font-weight: 600; }
    
    div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #4fc3f7; }
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────
SHEET_ID   = '1c2a-3t8fF2g_PX_0ape4ASTsbr5uX0Zb6YPzT8jtuN8'
SHEET_NAME = 'Sheet1'
SHEET_URL  = f'https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}'

FIELD_COLORS = {
    'Field-A (Corn)':    '#2196F3',
    'Field-B (Alfalfa)': '#4CAF50',
    'Field-C (Fallow)':  '#FF9800',
    'Field-D (Tomato)':  '#E91E63',
}

# ── Data Loader ────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)   # refresh every hour automatically
def load_data():
    df = pd.read_csv(SHEET_URL, low_memory=False)
    df.columns = (df.columns.str.strip()
                             .str.lower()
                             .str.replace(' ', '_')
                             .str.replace('(', '', regex=False)
                             .str.replace(')', '', regex=False))
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['timestamp']).sort_values('timestamp').reset_index(drop=True)
    num_cols = ['ndvi','ndwi','ndwi_real','savi','lai','fcover','lst','lst_modis',
                'kc','ks','dr','taw','raw','etc','water_need',
                'air_temp','humidity','solar_rad','precip','soil_temp','soil_moisture']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')
    df['hour']  = df['timestamp'].dt.floor('h')
    df['date']  = df['timestamp'].dt.date
    return df

# ── Header ─────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
  <h1>🛰️ AquaVolt-AI Live Telemetry</h1>
  <p>Physics-Informed Satellite-Driven Crop Water–Energy Optimization · UC Davis Russell Ranch, California</p>
  <p style='color:#b0bec5; font-size:0.85rem;'>Data updates every hour automatically · 256 sectors across 4 crop fields</p>
</div>
""", unsafe_allow_html=True)

# ── Load ───────────────────────────────────────────────────────────────────
with st.spinner('🛰️ Fetching live satellite telemetry...'):
    try:
        df = load_data()
        st.success(f'✅ Loaded **{len(df):,} records** · Latest: `{df["timestamp"].max()}`')
    except Exception as e:
        st.error(f'❌ Could not load data: {e}')
        st.stop()

# ── Sidebar Filters ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Filters")
    
    all_fields = sorted(df['field_name'].dropna().unique()) if 'field_name' in df.columns else []
    selected_fields = st.multiselect("🌾 Select Fields", all_fields, default=all_fields)
    
    date_min = df['date'].min()
    date_max = df['date'].max()
    date_range = st.date_input("📅 Date Range", value=(date_min, date_max),
                               min_value=date_min, max_value=date_max)
    
    st.markdown("---")
    st.markdown("### 📡 System Info")
    st.markdown(f"**Total Records:** `{len(df):,}`")
    st.markdown(f"**Fields:** `{len(all_fields)}`")
    st.markdown(f"**Date Range:** `{date_min}` → `{date_max}`")
    st.markdown(f"**Records/Hour:** `256`")
    st.markdown("---")
    st.markdown("[![GitHub](https://img.shields.io/badge/GitHub-aquavolt--ai--pk-black?logo=github)](https://github.com/umertanveer25/aquavolt-ai-pk)")
    st.markdown("[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/umertanveer25/aquavolt-ai-pk/blob/main/demo.ipynb)")

# ── Filter Data ────────────────────────────────────────────────────────────
if len(date_range) == 2:
    mask = (df['date'] >= date_range[0]) & (df['date'] <= date_range[1])
    df_f = df[mask]
else:
    df_f = df.copy()

if selected_fields and 'field_name' in df_f.columns:
    df_f = df_f[df_f['field_name'].isin(selected_fields)]

# ── KPI Metrics ────────────────────────────────────────────────────────────
st.markdown("### ⚡ Live Metrics (Latest Hour)")
latest_hour = df_f['hour'].max()
latest = df_f[df_f['hour'] == latest_hour]

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    st.metric("🌡️ Air Temp", f"{latest['air_temp'].mean():.1f}°C" if 'air_temp' in latest else "N/A")
with c2:
    st.metric("💧 Humidity", f"{latest['humidity'].mean():.0f}%" if 'humidity' in latest else "N/A")
with c3:
    st.metric("☀️ Solar Rad", f"{latest['solar_rad'].mean():.0f} W/m²" if 'solar_rad' in latest else "N/A")
with c4:
    st.metric("🌿 Avg NDVI", f"{latest['ndvi'].mean():.3f}" if 'ndvi' in latest else "N/A")
with c5:
    st.metric("💧 Avg ETc", f"{latest['etc'].mean():.2f} mm" if 'etc' in latest else "N/A")
with c6:
    st.metric("🚨 Water Deficit", f"{latest['water_need'].mean():.1f} mm" if 'water_need' in latest else "N/A")

st.markdown("---")

# ── Tabs ───────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "💧 Water Deficit",
    "🌿 Vegetation (NDVI)",
    "🗺️ Spatial Map",
    "🌡️ Weather",
    "📊 Correlation"
])

# ─── Tab 1: Water Deficit ──────────────────────────────────────────────────
with tab1:
    st.markdown("#### 💧 Hourly Water Deficit per Crop Field")
    if 'water_need' in df_f.columns and 'field_name' in df_f.columns:
        hourly = df_f.groupby(['hour','field_name'])['water_need'].mean().reset_index()
        fig, axes = plt.subplots(2, 2, figsize=(14, 8), facecolor='#0e1117')
        fig.patch.set_facecolor('#0e1117')
        axes = axes.flatten()
        
        for i, field in enumerate(selected_fields[:4]):
            ax = axes[i]
            ax.set_facecolor('#1a1a2e')
            data = hourly[hourly['field_name'] == field]
            color = FIELD_COLORS.get(field, '#4fc3f7')
            ax.fill_between(data['hour'], data['water_need'], alpha=0.25, color=color)
            ax.plot(data['hour'], data['water_need'], color=color, linewidth=2)
            if len(data) > 0:
                mean_v = data['water_need'].mean()
                ax.axhline(mean_v, linestyle='--', color='#ff7043', alpha=0.8,
                           label=f'Mean: {mean_v:.1f} mm')
                ax.legend(fontsize=9, facecolor='#1a1a2e', labelcolor='white')
            ax.set_title(field, color='white', fontsize=11, fontweight='bold')
            ax.set_ylabel('Water Deficit (mm)', color='#90a4ae')
            ax.tick_params(colors='#90a4ae', axis='both', labelsize=8)
            ax.tick_params(axis='x', rotation=30)
            for sp in ax.spines.values(): sp.set_edgecolor('#1e3a5f')
        
        for j in range(len(selected_fields), 4):
            axes[j].set_visible(False)
        
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

        # Summary table
        st.markdown("#### 📋 Field Summary (Selected Period)")
        summary = df_f.groupby('field_name')['water_need'].agg(
            Mean=lambda x: round(x.mean(), 2),
            Max=lambda x: round(x.max(), 2),
            Min=lambda x: round(x.min(), 2),
            Std=lambda x: round(x.std(), 2)
        ).reset_index()
        st.dataframe(summary, use_container_width=True, hide_index=True)

# ─── Tab 2: NDVI ──────────────────────────────────────────────────────────
with tab2:
    st.markdown("#### 🌿 NDVI Vegetation Index Over Time")
    if 'ndvi' in df_f.columns and 'field_name' in df_f.columns:
        fig, ax = plt.subplots(figsize=(14, 5), facecolor='#0e1117')
        ax.set_facecolor('#1a1a2e')
        
        hourly_ndvi = df_f.groupby(['hour','field_name'])['ndvi'].mean().reset_index()
        for field in selected_fields:
            data = hourly_ndvi[hourly_ndvi['field_name'] == field]
            color = FIELD_COLORS.get(field, '#4fc3f7')
            ax.plot(data['hour'], data['ndvi'], label=field, color=color, linewidth=2)
        
        ax.axhline(0.3, linestyle=':', color='orange', alpha=0.6, label='Stress Threshold (0.3)')
        ax.axhline(0.5, linestyle=':', color='#4CAF50', alpha=0.6, label='Healthy (0.5)')
        ax.set_ylabel('NDVI', color='#90a4ae')
        ax.set_xlabel('Time (UTC)', color='#90a4ae')
        ax.tick_params(colors='#90a4ae', labelsize=9)
        ax.tick_params(axis='x', rotation=30)
        ax.legend(facecolor='#1a1a2e', labelcolor='white', fontsize=9)
        ax.grid(True, alpha=0.15, color='#90a4ae')
        for sp in ax.spines.values(): sp.set_edgecolor('#1e3a5f')
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### 🌿 Current NDVI by Field")
            ndvi_now = latest.groupby('field_name')['ndvi'].mean().reset_index()
            ndvi_now.columns = ['Field', 'NDVI']
            ndvi_now['Status'] = ndvi_now['NDVI'].apply(
                lambda x: '🔴 Stressed' if x < 0.3 else ('🟡 Moderate' if x < 0.5 else '🟢 Healthy'))
            st.dataframe(ndvi_now, use_container_width=True, hide_index=True)

# ─── Tab 3: Spatial Map ───────────────────────────────────────────────────
with tab3:
    st.markdown(f"#### 🗺️ Spatial Water Stress Map — `{latest_hour.strftime('%Y-%m-%d %H:%M UTC')}`")
    if 'sector_row' in df_f.columns and 'sector_col' in df_f.columns:
        fig, axes = plt.subplots(1, min(4, len(selected_fields)),
                                 figsize=(5 * min(4, len(selected_fields)), 5),
                                 facecolor='#0e1117')
        if len(selected_fields) == 1:
            axes = [axes]
        
        for i, field in enumerate(selected_fields[:4]):
            ax = axes[i]
            ax.set_facecolor('#1a1a2e')
            fdata = latest[latest['field_name'] == field]
            if len(fdata) > 0:
                try:
                    pivot = fdata.pivot_table(
                        index='sector_row', columns='sector_col',
                        values='water_need', aggfunc='mean')
                    sns.heatmap(pivot, ax=ax, cmap='YlOrRd', annot=True, fmt='.0f',
                                linewidths=0.5, linecolor='#0e1117',
                                cbar_kws={'label': 'Water Deficit (mm)', 'shrink': 0.8},
                                annot_kws={'size': 7, 'color': 'black'})
                    ax.set_title(field, color='white', fontsize=10, fontweight='bold')
                    ax.tick_params(colors='#90a4ae', labelsize=8)
                except Exception as e:
                    ax.text(0.5, 0.5, f'No data', ha='center', va='center',
                            color='white', transform=ax.transAxes)
        
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()
        st.caption("Each cell = one 8×8 grid sector. Color = water deficit intensity. Red = high stress.")

# ─── Tab 4: Weather ───────────────────────────────────────────────────────
with tab4:
    st.markdown("#### 🌡️ Weather Variables Over Time")
    weather_cols = [c for c in ['air_temp','humidity','solar_rad','soil_moisture'] if c in df_f.columns]
    labels = {'air_temp': '🌡️ Air Temp (°C)', 'humidity': '💧 Humidity (%)',
              'solar_rad': '☀️ Solar Rad (W/m²)', 'soil_moisture': '🌱 Soil Moisture'}
    colors_w = ['#ef5350','#42a5f5','#ffca28','#66bb6a']
    
    if weather_cols:
        hourly_w = df_f.groupby('hour')[weather_cols].mean().reset_index()
        fig, axes = plt.subplots(len(weather_cols), 1,
                                 figsize=(14, 3.5 * len(weather_cols)),
                                 facecolor='#0e1117')
        if len(weather_cols) == 1:
            axes = [axes]
        
        for i, (col, color) in enumerate(zip(weather_cols, colors_w)):
            ax = axes[i]
            ax.set_facecolor('#1a1a2e')
            ax.fill_between(hourly_w['hour'], hourly_w[col], alpha=0.2, color=color)
            ax.plot(hourly_w['hour'], hourly_w[col], color=color, linewidth=2)
            ax.set_ylabel(labels.get(col, col), color='#90a4ae')
            ax.tick_params(colors='#90a4ae', labelsize=8)
            ax.tick_params(axis='x', rotation=30)
            ax.grid(True, alpha=0.15, color='#90a4ae')
            for sp in ax.spines.values(): sp.set_edgecolor('#1e3a5f')
        
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

# ─── Tab 5: Correlation ───────────────────────────────────────────────────
with tab5:
    st.markdown("#### 📊 Variable Correlation Matrix")
    corr_cols = [c for c in ['ndvi','ndwi','etc','water_need','air_temp',
                              'humidity','solar_rad','soil_moisture','kc','ks'] if c in df_f.columns]
    if len(corr_cols) >= 4:
        fig, ax = plt.subplots(figsize=(11, 9), facecolor='#0e1117')
        ax.set_facecolor('#1a1a2e')
        corr = df_f[corr_cols].corr()
        mask = np.triu(np.ones_like(corr, dtype=bool))
        sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='RdYlGn', center=0,
                    square=True, linewidths=0.5, linecolor='#0e1117',
                    cbar_kws={'shrink': 0.8}, ax=ax, annot_kws={'size': 10})
        ax.tick_params(colors='#90a4ae')
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close()

# ── Footer ─────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style='text-align:center; color:#546e7a; font-size:0.85rem; padding:1rem 0'>
  🛰️ <strong>AquaVolt-AI</strong> · Physics-Informed Satellite Crop Monitoring ·
  <strong>Umer Tanveer</strong>, PhD Candidate, AWKUM Pakistan<br>
  Data refreshes every hour automatically via GitHub Actions + FAO-56 Penman-Monteith
</div>
""", unsafe_allow_html=True)
