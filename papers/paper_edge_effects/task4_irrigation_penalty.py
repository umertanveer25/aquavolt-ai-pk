"""
Paper 3 -- Task 4: Irrigation Penalty Calculation
How much extra water (mm/day) do edge sectors need vs core sectors?
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
df = df.dropna(subset=['field_name', 'lst', 'air_temp', 'sector_row', 'sector_col', 'ETc', 'water_need', 'Dr'])

df['delta_T'] = df['lst'] - df['air_temp']
df['date'] = pd.to_datetime(df['timestamp']).dt.date
df['dist_to_edge'] = df.apply(
    lambda r: min(r['sector_row'], 7 - r['sector_row'],
                  r['sector_col'], 7 - r['sector_col']), axis=1)

FIELDS = ['Field-A (Corn)', 'Field-B (Alfalfa)', 'Field-D (Tomato)']
LABELS = {'Field-A (Corn)': 'Corn', 'Field-B (Alfalfa)': 'Alfalfa', 'Field-D (Tomato)': 'Tomato'}
COLORS = {'Field-A (Corn)': '#2196F3', 'Field-B (Alfalfa)': '#4CAF50', 'Field-D (Tomato)': '#F44336'}

print("\n=== IRRIGATION PENALTY ANALYSIS ===")
print("(How much extra water do edge sectors consume vs core?)\n")

fig, axes = plt.subplots(2, 3, figsize=(20, 12))

for i, field in enumerate(FIELDS):
    crop = LABELS[field]
    fd = df[df['field_name'] == field]
    
    # ETc by distance band
    etc_by_dist = fd.groupby('dist_to_edge')['ETc'].mean()
    dr_by_dist = fd.groupby('dist_to_edge')['Dr'].mean()
    wn_by_dist = fd.groupby('dist_to_edge')['water_need'].mean()
    
    edge_etc = fd[fd['dist_to_edge'] == 0]['ETc'].mean()
    core_etc = fd[fd['dist_to_edge'] >= 3]['ETc'].mean()
    etc_penalty = edge_etc - core_etc
    
    edge_dr = fd[fd['dist_to_edge'] == 0]['Dr'].mean()
    core_dr = fd[fd['dist_to_edge'] >= 3]['Dr'].mean()
    dr_penalty = edge_dr - core_dr
    
    edge_wn = fd[fd['dist_to_edge'] == 0]['water_need'].mean()
    core_wn = fd[fd['dist_to_edge'] >= 3]['water_need'].mean()
    wn_penalty = edge_wn - core_wn
    
    # T-test on ETc
    edge_vals = fd[fd['dist_to_edge'] == 0]['ETc']
    core_vals = fd[fd['dist_to_edge'] >= 3]['ETc']
    t_stat, t_p = stats.ttest_ind(edge_vals, core_vals, equal_var=False)
    
    print(f"  {crop}:")
    print(f"    Edge ETc      = {edge_etc:.3f} mm/hr    Core ETc      = {core_etc:.3f} mm/hr    Penalty = {etc_penalty:+.3f} mm/hr")
    print(f"    Edge Dr       = {edge_dr:.3f} mm       Core Dr       = {core_dr:.3f} mm       Penalty = {dr_penalty:+.3f} mm")
    print(f"    Edge WaterNeed= {edge_wn:.3f} mm       Core WaterNeed= {core_wn:.3f} mm       Penalty = {wn_penalty:+.3f} mm")
    print(f"    ETc t-test: t = {t_stat:.4f}, p = {t_p:.2e}")
    
    # Daily irrigation penalty
    daily_edge = fd[fd['dist_to_edge'] == 0].groupby('date')['ETc'].sum()
    daily_core = fd[fd['dist_to_edge'] >= 3].groupby('date')['ETc'].sum()
    # Normalize by number of sectors
    n_edge_sectors = fd[fd['dist_to_edge'] == 0].groupby('date')['sector_row'].nunique().mean() * \
                     fd[fd['dist_to_edge'] == 0].groupby('date')['sector_col'].nunique().mean()
    n_core_sectors = fd[fd['dist_to_edge'] >= 3].groupby('date')['sector_row'].nunique().mean() * \
                     fd[fd['dist_to_edge'] >= 3].groupby('date')['sector_col'].nunique().mean()
    
    daily_penalty_pct = ((edge_etc - core_etc) / core_etc * 100) if core_etc > 0 else 0
    print(f"    Daily ETc penalty: {daily_penalty_pct:+.1f}% more water at edges\n")
    
    # Plot 1: ETc by distance
    axes[0, i].bar(etc_by_dist.index * 10, etc_by_dist.values, color=COLORS[field],
                   edgecolor='black', linewidth=0.5)
    axes[0, i].set_title(f'{crop} - ETc by Distance', fontsize=13, fontweight='bold')
    axes[0, i].set_xlabel('Distance from Edge (m)')
    axes[0, i].set_ylabel('Mean ETc (mm/hr)')
    axes[0, i].grid(True, alpha=0.3, axis='y')
    
    # Plot 2: Dr (depletion) by distance
    axes[1, i].bar(dr_by_dist.index * 10, dr_by_dist.values, color=COLORS[field],
                   edgecolor='black', linewidth=0.5, alpha=0.7)
    axes[1, i].set_title(f'{crop} - Root-Zone Depletion by Distance', fontsize=13, fontweight='bold')
    axes[1, i].set_xlabel('Distance from Edge (m)')
    axes[1, i].set_ylabel('Mean Dr (mm)')
    axes[1, i].grid(True, alpha=0.3, axis='y')

plt.suptitle('Irrigation Water Penalty: Edge vs Core Sectors', fontsize=15, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{OUT}/fig10_irrigation_penalty.png', bbox_inches='tight', dpi=300)
print("Saved fig10_irrigation_penalty.png")
print("\nDONE - Irrigation penalty analysis complete.")
