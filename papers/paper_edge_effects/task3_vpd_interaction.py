"""
Paper 3 -- Task 3: VPD x Edge Interaction Analysis
Does the edge effect amplify on high-VPD days?
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

DATA = r'C:\Users\umert\Downloads\AquaVolt-AI Telemetry Log (1).xlsx'
OUT = r'C:\Users\umert\aquavolt-ai-pk\papers\paper_edge_effects\figures'

print("Loading data...")
df = pd.read_excel(DATA)
df = df[df['field_name'] != 'Field-C (Fallow)']
df = df[df['scene_id'] != 'Fallback']
df = df.dropna(subset=['field_name', 'lst', 'air_temp', 'sector_row', 'sector_col', 'humidity'])

df['delta_T'] = df['lst'] - df['air_temp']
df['es'] = 0.6108 * np.exp(17.27 * df['air_temp'] / (df['air_temp'] + 237.3))
df['ea'] = df['es'] * df['humidity'] / 100.0
df['vpd'] = df['es'] - df['ea']
df['date'] = pd.to_datetime(df['timestamp']).dt.date
df['dist_to_edge'] = df.apply(
    lambda r: min(r['sector_row'], 7 - r['sector_row'],
                  r['sector_col'], 7 - r['sector_col']), axis=1)

FIELDS = ['Field-A (Corn)', 'Field-B (Alfalfa)', 'Field-D (Tomato)']
LABELS = {'Field-A (Corn)': 'Corn', 'Field-B (Alfalfa)': 'Alfalfa', 'Field-D (Tomato)': 'Tomato'}
COLORS = {'Field-A (Corn)': '#2196F3', 'Field-B (Alfalfa)': '#4CAF50', 'Field-D (Tomato)': '#F44336'}

print("\n=== VPD x EDGE INTERACTION ===")

# Daily edge-core diff vs daily mean VPD
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
results = {}

for i, field in enumerate(FIELDS):
    crop = LABELS[field]
    fd = df[df['field_name'] == field]
    
    daily = []
    for date, gd in fd.groupby('date'):
        edge_dT = gd[gd['dist_to_edge'] == 0]['delta_T'].mean()
        core_dT = gd[gd['dist_to_edge'] >= 3]['delta_T'].mean()
        vpd_mean = gd['vpd'].mean()
        daily.append({'date': date, 'edge_core_diff': edge_dT - core_dT, 'vpd': vpd_mean})
    
    ddf = pd.DataFrame(daily).dropna()
    
    # Pearson correlation
    r_val, p_val = stats.pearsonr(ddf['vpd'], ddf['edge_core_diff'])
    slope, intercept, _, _, se = stats.linregress(ddf['vpd'], ddf['edge_core_diff'])
    
    print(f"\n  {crop}:")
    print(f"    Daily VPD range: {ddf['vpd'].min():.2f} - {ddf['vpd'].max():.2f} kPa")
    print(f"    Pearson r(VPD, Edge-Core diff) = {r_val:.4f}, p = {p_val:.2e}")
    print(f"    Regression slope = {slope:.4f} C/kPa")
    
    results[crop] = {'pearson_r': round(r_val, 4), 'pearson_p': float(f"{p_val:.2e}"),
                     'slope': round(slope, 4)}
    
    # Scatter plot
    axes[i].scatter(ddf['vpd'], ddf['edge_core_diff'], s=60, color=COLORS[field], 
                    edgecolors='black', linewidth=0.5, alpha=0.8)
    x_fit = np.linspace(ddf['vpd'].min(), ddf['vpd'].max(), 100)
    axes[i].plot(x_fit, slope * x_fit + intercept, '--', color='black', linewidth=2,
                 label=f'r={r_val:.3f}, p={p_val:.2e}')
    axes[i].axhline(y=0, color='gray', linestyle=':', alpha=0.5)
    axes[i].set_title(f'{crop}', fontsize=14, fontweight='bold')
    axes[i].set_xlabel('Daily Mean VPD (kPa)')
    axes[i].set_ylabel('Edge - Core $\\Delta T$ (C)')
    axes[i].legend(fontsize=9)
    axes[i].grid(True, alpha=0.3)

plt.suptitle('VPD x Edge Interaction: Does High VPD Amplify the Edge Effect?',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{OUT}/fig9_vpd_edge_interaction.png', bbox_inches='tight', dpi=300)
print("\nSaved fig9_vpd_edge_interaction.png")

# VPD tercile analysis
print("\n=== VPD TERCILE ANALYSIS ===")
for field in FIELDS:
    crop = LABELS[field]
    fd = df[df['field_name'] == field].copy()
    fd['vpd_tercile'] = pd.qcut(fd['vpd'], 3, labels=['Low VPD', 'Mid VPD', 'High VPD'])
    
    print(f"\n  {crop}:")
    for tercile in ['Low VPD', 'Mid VPD', 'High VPD']:
        td = fd[fd['vpd_tercile'] == tercile]
        edge_dT = td[td['dist_to_edge'] == 0]['delta_T'].mean()
        core_dT = td[td['dist_to_edge'] >= 3]['delta_T'].mean()
        diff = edge_dT - core_dT
        print(f"    {tercile:10s}: Edge-Core diff = {diff:+.3f} C  (edge={edge_dT:.2f}, core={core_dT:.2f})")

print("\nDONE - VPD x Edge interaction analysis complete.")
