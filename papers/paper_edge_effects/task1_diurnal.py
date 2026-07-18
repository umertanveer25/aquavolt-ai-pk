"""
Paper 3 — Task 1: Diurnal Edge-Core Gradient Analysis
How does the edge-core temperature difference change hour-by-hour?
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

DATA = r'C:\Users\umert\Downloads\AquaVolt-AI Telemetry Log (1).xlsx'
OUT = r'C:\Users\umert\aquavolt-ai-pk\papers\paper_edge_effects\figures'

print("Loading data...")
df = pd.read_excel(DATA)
df = df[df['field_name'] != 'Field-C (Fallow)']
df = df[df['scene_id'] != 'Fallback']
df = df.dropna(subset=['field_name', 'lst', 'air_temp', 'sector_row', 'sector_col', 'timestamp'])

df['delta_T'] = df['lst'] - df['air_temp']
df['hour'] = pd.to_datetime(df['timestamp']).dt.hour
df['dist_to_edge'] = df.apply(
    lambda r: min(r['sector_row'], 7 - r['sector_row'],
                  r['sector_col'], 7 - r['sector_col']), axis=1)
df['is_edge'] = (df['dist_to_edge'] == 0).astype(int)
df['is_core'] = (df['dist_to_edge'] >= 3).astype(int)

FIELDS = ['Field-A (Corn)', 'Field-B (Alfalfa)', 'Field-D (Tomato)']
LABELS = {'Field-A (Corn)': 'Corn', 'Field-B (Alfalfa)': 'Alfalfa', 'Field-D (Tomato)': 'Tomato'}
COLORS = {'Field-A (Corn)': '#2196F3', 'Field-B (Alfalfa)': '#4CAF50', 'Field-D (Tomato)': '#F44336'}

# Compute hourly edge-core gradient
fig, axes = plt.subplots(1, 3, figsize=(20, 6))
print("\n=== DIURNAL EDGE-CORE GRADIENT ===")

for i, field in enumerate(FIELDS):
    fd = df[df['field_name'] == field]
    hourly = []
    for hour in sorted(fd['hour'].unique()):
        hd = fd[fd['hour'] == hour]
        edge_mean = hd[hd['is_edge'] == 1]['delta_T'].mean()
        core_mean = hd[hd['is_core'] == 1]['delta_T'].mean()
        diff = edge_mean - core_mean
        hourly.append({'hour': hour, 'edge_dT': edge_mean, 'core_dT': core_mean, 'diff': diff})
        
    hdf = pd.DataFrame(hourly)
    
    ax = axes[i]
    ax.plot(hdf['hour'], hdf['edge_dT'], 'o-', color='red', linewidth=2, label='Edge (0m)')
    ax.plot(hdf['hour'], hdf['core_dT'], 's-', color='blue', linewidth=2, label='Core (30m+)')
    ax.fill_between(hdf['hour'], hdf['edge_dT'], hdf['core_dT'], alpha=0.2, color='orange')
    ax.set_title(f'{LABELS[field]}', fontsize=14, fontweight='bold')
    ax.set_xlabel('Hour of Day (UTC)')
    ax.set_ylabel('Mean $\\Delta T$ (C)')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    peak_hour = hdf.loc[hdf['diff'].abs().idxmax()]
    print(f"  {LABELS[field]}: Peak gradient at hour {int(peak_hour['hour'])}:00 UTC")
    print(f"    Edge dT={peak_hour['edge_dT']:.2f}, Core dT={peak_hour['core_dT']:.2f}, Diff={peak_hour['diff']:.2f} C")

plt.suptitle('Diurnal Variation of Edge vs Core Thermal Anomaly', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{OUT}/fig6_diurnal_gradient.png', bbox_inches='tight', dpi=300)
print("Saved fig6_diurnal_gradient.png")

# Also plot the gradient itself
fig2, ax2 = plt.subplots(figsize=(10, 6))
for field in FIELDS:
    fd = df[df['field_name'] == field]
    hourly = []
    for hour in sorted(fd['hour'].unique()):
        hd = fd[fd['hour'] == hour]
        edge_mean = hd[hd['is_edge'] == 1]['delta_T'].mean()
        core_mean = hd[hd['is_core'] == 1]['delta_T'].mean()
        hourly.append({'hour': hour, 'diff': edge_mean - core_mean})
    hdf = pd.DataFrame(hourly)
    ax2.plot(hdf['hour'], hdf['diff'], 'o-', color=COLORS[field], linewidth=2, label=LABELS[field])

ax2.axhline(y=0, color='black', linestyle='--', alpha=0.5)
ax2.set_xlabel('Hour of Day (UTC)', fontsize=12)
ax2.set_ylabel('Edge - Core $\\Delta T$ Difference (C)', fontsize=12)
ax2.set_title('Diurnal Edge-Core Temperature Gradient by Crop Type', fontsize=14, fontweight='bold')
ax2.legend(title='Crop', fontsize=11)
ax2.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(f'{OUT}/fig7_diurnal_diff.png', bbox_inches='tight', dpi=300)
print("Saved fig7_diurnal_diff.png")
print("DONE - Diurnal analysis complete.")
