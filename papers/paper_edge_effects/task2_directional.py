"""
Paper 3 -- Task 2: Directional Asymmetry Analysis
Which side (N/S/E/W) of each field is hottest?
The side facing the fallow field should be significantly hotter.
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
df = df.dropna(subset=['field_name', 'lst', 'air_temp', 'sector_row', 'sector_col'])
df['delta_T'] = df['lst'] - df['air_temp']

# Assign directional edge labels
# In an 8x8 grid (0-7): row=0 is North edge, row=7 is South edge
# col=0 is West edge, col=7 is East edge
def get_edge_direction(row, col):
    directions = []
    if row == 0: directions.append('North')
    if row == 7: directions.append('South')
    if col == 0: directions.append('West')
    if col == 7: directions.append('East')
    if not directions: return 'Interior'
    return '/'.join(directions)

df['edge_dir'] = df.apply(lambda r: get_edge_direction(int(r['sector_row']), int(r['sector_col'])), axis=1)

FIELDS = ['Field-A (Corn)', 'Field-B (Alfalfa)', 'Field-D (Tomato)']
LABELS = {'Field-A (Corn)': 'Corn', 'Field-B (Alfalfa)': 'Alfalfa', 'Field-D (Tomato)': 'Tomato'}

print("\n=== DIRECTIONAL ASYMMETRY ANALYSIS ===")
fig, axes = plt.subplots(1, 3, figsize=(20, 6))
dir_order = ['North', 'South', 'East', 'West', 'Interior']

for i, field in enumerate(FIELDS):
    crop = LABELS[field]
    fd = df[df['field_name'] == field]
    
    # Only pure single-direction edges (exclude corners)
    fd_edges = fd[fd['edge_dir'].isin(['North', 'South', 'East', 'West', 'Interior'])]
    
    print(f"\n  {crop}:")
    dir_means = {}
    for d in ['North', 'South', 'East', 'West', 'Interior']:
        vals = fd_edges[fd_edges['edge_dir'] == d]['delta_T']
        if len(vals) > 0:
            dir_means[d] = vals.mean()
            print(f"    {d:10s}: mean dT = {vals.mean():.3f} C  (n={len(vals):,})")
    
    # ANOVA across directions
    groups = [fd_edges[fd_edges['edge_dir'] == d]['delta_T'].values 
              for d in ['North', 'South', 'East', 'West'] 
              if len(fd_edges[fd_edges['edge_dir'] == d]) > 0]
    if len(groups) >= 2:
        f_stat, p_val = stats.f_oneway(*groups)
        print(f"    ANOVA (edges only): F = {f_stat:.4f}, p = {p_val:.2e}")
    
    # Find hottest direction
    if dir_means:
        hottest = max({k: v for k, v in dir_means.items() if k != 'Interior'}, key=lambda k: dir_means[k])
        print(f"    >> HOTTEST EDGE: {hottest} ({dir_means[hottest]:.3f} C)")
    
    # Bar plot
    plot_data = fd_edges[fd_edges['edge_dir'].isin(dir_order)]
    means = plot_data.groupby('edge_dir')['delta_T'].mean().reindex(dir_order).dropna()
    sems = plot_data.groupby('edge_dir')['delta_T'].sem().reindex(dir_order).dropna()
    
    colors_map = {'North': '#E53935', 'South': '#1E88E5', 'East': '#FDD835', 'West': '#43A047', 'Interior': '#9E9E9E'}
    bar_colors = [colors_map.get(d, '#9E9E9E') for d in means.index]
    
    axes[i].bar(means.index, means.values, yerr=1.96*sems.values, capsize=4, 
                color=bar_colors, edgecolor='black', linewidth=0.5)
    axes[i].set_title(f'{crop}', fontsize=14, fontweight='bold')
    axes[i].set_ylabel('Mean $\\Delta T$ (C)')
    axes[i].set_xlabel('Edge Direction')
    axes[i].tick_params(axis='x', rotation=30)
    axes[i].grid(True, alpha=0.3, axis='y')

plt.suptitle('Directional Asymmetry: Mean Thermal Anomaly by Field Edge', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(f'{OUT}/fig8_directional_asymmetry.png', bbox_inches='tight', dpi=300)
print("\nSaved fig8_directional_asymmetry.png")
print("DONE - Directional asymmetry analysis complete.")
