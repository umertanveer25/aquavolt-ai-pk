import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import chi2_contingency
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap
import warnings, os
warnings.filterwarnings('ignore')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FIGURES_DIR = os.path.join(BASE_DIR, "figures")
os.makedirs(FIGURES_DIR, exist_ok=True)

# ─── Load & clean ────────────────────────────────────────────────────────────
print("Loading telemetry data...")
xlsx_path = os.path.join(BASE_DIR, "data", "AquaVolt-AI Telemetry Log (1).xlsx")
df = pd.read_excel(xlsx_path, engine='openpyxl')
df['datetime'] = pd.to_datetime(df['timestamp'])
df = df[df['scene_id'] != 'Fallback']
df = df[~df['field_name'].str.contains('Fallow', na=False)]
df = df.groupby(['timestamp', 'field_name', 'sector_row', 'sector_col'], as_index=False).mean(numeric_only=True)
df['field_name'] = df['field_name'].astype(str)
df['datetime'] = pd.to_datetime(df['timestamp'])

df['es'] = 0.6108 * np.exp(17.27 * df['air_temp'] / (df['air_temp'] + 237.3))
df['ea'] = df['es'] * df['humidity'] / 100
df['VPD'] = df['es'] - df['ea']
df['delta_T'] = df['lst'] - df['air_temp']

def classify_stress(row):
    ks_stressed = row['Ks'] < 1.0
    thermal_stressed = row['delta_T'] >= 2.0
    vpd_high = row['VPD'] >= 1.5
    if not ks_stressed and not thermal_stressed:
        return 'No Stress'
    elif ks_stressed and thermal_stressed:
        return 'Coupled Root-Zone Stress'
    elif not ks_stressed and thermal_stressed and vpd_high:
        return 'Decoupled Atmospheric Stress'
    elif ks_stressed and not thermal_stressed:
        return 'Masked Hidden Stress'
    else:
        return 'No Stress'

df['stress_class'] = df.apply(classify_stress, axis=1)
crop_map = {'Field-A (Corn)': 'Corn', 'Field-B (Alfalfa)': 'Alfalfa', 'Field-D (Tomato)': 'Tomato'}
df['crop'] = df['field_name'].map(crop_map)
df = df[df['crop'].notna()]

# ─── Print real counts ────────────────────────────────────────────────────────
print(f"\nTotal records: {len(df)}")
counts = df['stress_class'].value_counts()
pcts   = df['stress_class'].value_counts(normalize=True) * 100
print("\n=== REAL STRESS CLASS COUNTS ===")
for idx in counts.index:
    print(f"  {idx}: {counts[idx]:,} ({pcts[idx]:.2f}%)")

print("\n=== REAL DSI BY CROP ===")
dsi_results = {}
for crop in ['Corn', 'Alfalfa', 'Tomato']:
    sub = df[df['crop'] == crop]
    stress    = sub[sub['stress_class'] != 'No Stress']
    decoupled = sub[sub['stress_class'] == 'Decoupled Atmospheric Stress']
    dsi = len(decoupled) / len(stress) if len(stress) > 0 else 0
    dsi_results[crop] = dsi
    print(f"  {crop}: total={len(sub):,} | stress={len(stress):,} | decoupled={len(decoupled):,} | DSI={dsi:.4f}")

# ─── Chi-square ───────────────────────────────────────────────────────────────
print("\n=== CHI-SQUARE: Stress class × Crop ===")
cats = ['No Stress','Coupled Root-Zone Stress','Decoupled Atmospheric Stress','Masked Hidden Stress']
crops_list = ['Corn','Alfalfa','Tomato']
contingency = np.array([[len(df[(df['crop']==c) & (df['stress_class']==cat)])
                         for cat in cats] for c in crops_list])
chi2_val, p_chi2, dof, _ = chi2_contingency(contingency)
print(f"  chi2={chi2_val:.2f}, df={dof}, p={p_chi2:.6e}")

# Pairwise (Corn only has decoupled, so just compare Corn vs others combined)
corn_dec   = len(df[(df['crop']=='Corn') & (df['stress_class']=='Decoupled Atmospheric Stress')])
corn_ndec  = len(df[(df['crop']=='Corn') & (df['stress_class']!='Decoupled Atmospheric Stress')])
other_dec  = len(df[(df['crop']!='Corn') & (df['stress_class']=='Decoupled Atmospheric Stress')])
other_ndec = len(df[(df['crop']!='Corn') & (df['stress_class']!='Decoupled Atmospheric Stress')])
table2 = np.array([[corn_dec, corn_ndec],[other_dec+1, other_ndec]])  # +1 for zero-cell correction
chi2_pw, p_pw, _, _ = chi2_contingency(table2)
print(f"  Corn vs Others (decoupled): chi2={chi2_pw:.2f}, p={p_pw:.6e}")

# ─── Logistic Regression: VPD → P(Decoupled) – Corn only ─────────────────────
print("\n=== LOGISTIC REGRESSION: VPD -> P(Decoupled) [Corn only] ===")
sub_corn = df[df['crop'] == 'Corn'].copy()
sub_corn['is_decoupled'] = (sub_corn['stress_class'] == 'Decoupled Atmospheric Stress').astype(int)
X_corn = sub_corn[['VPD']].values
y_corn = sub_corn['is_decoupled'].values
clf_corn = LogisticRegression(max_iter=1000).fit(X_corn, y_corn)
prob_corn = clf_corn.predict_proba(X_corn)[:, 1]
auc_corn = roc_auc_score(y_corn, prob_corn)
beta_corn = clf_corn.coef_[0][0]
print(f"  Corn: beta={beta_corn:.4f}, AUC={auc_corn:.4f}")

# ─── Pearson r: Daily VPD vs Daily DSI ───────────────────────────────────────
print("\n=== PEARSON r: Daily VPD vs Daily DSI ===")
df['date'] = df['datetime'].dt.date
daily = []
for date, grp in df.groupby('date'):
    stress    = grp[grp['stress_class'] != 'No Stress']
    decoupled = grp[grp['stress_class'] == 'Decoupled Atmospheric Stress']
    dsi_d = len(decoupled) / len(stress) if len(stress) > 0 else 0
    daily.append({'date': date, 'DSI': dsi_d, 'VPD': grp['VPD'].mean()})
daily_df = pd.DataFrame(daily)
r_val, p_r = stats.pearsonr(daily_df['VPD'], daily_df['DSI'])
print(f"  r={r_val:.4f}, p={p_r:.6f}, n_days={len(daily_df)}")

# ─── ICC approximation ───────────────────────────────────────────────────────
print("\n=== ICC BY CROP ===")
icc_results = {}
for field, crop in [('Field-A (Corn)','Corn'),('Field-B (Alfalfa)','Alfalfa'),('Field-D (Tomato)','Tomato')]:
    sub = df[df['field_name'] == field].copy()
    sub['is_decoupled'] = (sub['stress_class'] == 'Decoupled Atmospheric Stress').astype(float)
    sector_means = sub.groupby(['sector_row','sector_col'])['is_decoupled'].mean()
    between_var  = sector_means.var()
    total_var    = sub['is_decoupled'].var()
    icc = between_var / total_var if total_var > 0 else 0
    icc_results[crop] = icc
    print(f"  {crop}: ICC={icc:.4f}")

# ─── Border vs Interior DSI t-test (Corn only meaningful) ────────────────────
print("\n=== BORDER vs INTERIOR DSI (Corn) ===")
sub_corn_grid = df[df['field_name'] == 'Field-A (Corn)']
grid = {}
for (r_, c_), grp in sub_corn_grid.groupby(['sector_row','sector_col']):
    stress    = grp[grp['stress_class'] != 'No Stress']
    decoupled = grp[grp['stress_class'] == 'Decoupled Atmospheric Stress']
    grid[(r_, c_)] = len(decoupled) / len(stress) if len(stress) > 0 else 0
border   = [v for (r_,c_),v in grid.items() if r_ in [0,7] or c_ in [0,7]]
interior = [v for (r_,c_),v in grid.items() if r_ not in [0,7] and c_ not in [0,7]]
t_val, p_t = stats.ttest_ind(border, interior)
print(f"  Border mean={np.mean(border):.4f}, Interior mean={np.mean(interior):.4f}, t={t_val:.3f}, p={p_t:.4f}")

# ─── SUMMARY JSON for paper update ───────────────────────────────────────────
import json
summary = {
    'total_records': int(len(df)),
    'stress_counts': {k: int(v) for k, v in counts.items()},
    'stress_pcts':   {k: float(f'{v:.2f}') for k, v in pcts.items()},
    'dsi': {k: float(f'{v:.4f}') for k, v in dsi_results.items()},
    'chi2_overall': float(f'{chi2_val:.2f}'),
    'chi2_p': float(f'{p_chi2:.2e}'),
    'chi2_dof': int(dof),
    'chi2_corn_vs_others': float(f'{chi2_pw:.2f}'),
    'chi2_pw_p': float(f'{p_pw:.2e}'),
    'lr_corn_beta': float(f'{beta_corn:.4f}'),
    'lr_corn_auc': float(f'{auc_corn:.4f}'),
    'pearson_r': float(f'{r_val:.4f}'),
    'pearson_p': float(f'{p_r:.6f}'),
    'pearson_n': int(len(daily_df)),
    'icc': {k: float(f'{v:.4f}') for k, v in icc_results.items()},
    'border_dsi_mean': float(f'{np.mean(border):.4f}'),
    'interior_dsi_mean': float(f'{np.mean(interior):.4f}'),
    'border_interior_t': float(f'{t_val:.3f}'),
    'border_interior_p': float(f'{p_t:.4f}'),
}
stats_json_path = os.path.join(BASE_DIR, "real_stats.json")
with open(stats_json_path, 'w') as f:
    json.dump(summary, f, indent=2)
print("\n=== SAVED TO real_stats.json ===")

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 2: Scatter plot (VPD vs Soil Moisture, real data)
# ═══════════════════════════════════════════════════════════════════════════
print("\nGenerating Figure 2 (real data)...")
sample = df.sample(min(10000, len(df)), random_state=42)
color_map = {
    'No Stress': '#2ecc71',
    'Coupled Root-Zone Stress': '#e74c3c',
    'Decoupled Atmospheric Stress': '#f39c12',
    'Masked Hidden Stress': '#9b59b6'
}
fig, axes = plt.subplots(1, 3, figsize=(16, 5), sharey=True)
for ax, crop in zip(axes, ['Corn', 'Alfalfa', 'Tomato']):
    crop_df = sample[sample['crop'] == crop]
    for sc, color in color_map.items():
        mask = crop_df['stress_class'] == sc
        n = mask.sum()
        ax.scatter(crop_df.loc[mask, 'soil_moisture'], crop_df.loc[mask, 'VPD'],
                   c=color, s=10, alpha=0.5, label=f'{sc} (n={n:,})', edgecolors='none')
    ax.axhline(y=1.5, color='#e74c3c', linestyle='--', lw=1.5, alpha=0.8)
    ax.axvline(x=0.10, color='#3498db', linestyle='--', lw=1.5, alpha=0.8)
    ax.set_title(crop, fontsize=10, fontweight='bold')
    ax.set_xlabel('Soil Moisture (m³/m³)', fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.set_facecolor('#f8f9fa')
    ax.legend(fontsize=6, loc='upper right')
axes[0].set_ylabel('VPD (kPa)', fontsize=9)
fig.suptitle('Figure 2: Real Stress Classification in VPD–Soil Moisture Space (n=72,768 sector-hours)',
             fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{FIGURES_DIR}/fig2_stress_scatter.png", dpi=200, bbox_inches='tight')
plt.savefig(f"{FIGURES_DIR}/fig2_stress_scatter.pdf", dpi=200, bbox_inches='tight')
plt.close()
print("Figure 2 done.")

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 3: DSI bar chart (real values)
# ═══════════════════════════════════════════════════════════════════════════
print("Generating Figure 3 (real data)...")
crops_list2 = ['Corn', 'Alfalfa', 'Tomato']
real_dsi = [dsi_results[c] for c in crops_list2]
real_pcts_by_crop = {}
for crop in crops_list2:
    sub = df[df['crop'] == crop]
    real_pcts_by_crop[crop] = {cat: len(sub[sub['stress_class']==cat])/len(sub)*100 for cat in cats}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
x = np.arange(3)
width = 0.18
colors_bar = ['#2ecc71', '#e74c3c', '#f39c12', '#9b59b6']
crop_labels_short = ['Corn\n(Z. mays)', 'Alfalfa\n(M. sativa)', 'Tomato\n(S. lycopersicum)']
for i, (cat, color) in enumerate(zip(cats, colors_bar)):
    vals = [real_pcts_by_crop[c][cat] for c in crops_list2]
    ax1.bar(x + i*width, vals, width, label=cat, color=color, alpha=0.88, edgecolor='white')
ax1.set_xticks(x + width*1.5)
ax1.set_xticklabels(crop_labels_short, fontsize=9)
ax1.set_ylabel('Percentage of Sector-Hours (%)', fontsize=9)
ax1.set_title('Real Stress Category Distribution by Crop\n(n=72,768 sector-hours)', fontsize=9.5, fontweight='bold')
ax1.legend(fontsize=7, loc='upper right')
ax1.grid(axis='y', alpha=0.3)
ax1.set_facecolor('#f8f9fa')
bars = ax2.bar(crop_labels_short, real_dsi,
               color=['#e67e22', '#27ae60', '#e74c3c'], alpha=0.88, edgecolor='white', width=0.5)
for bar, val in zip(bars, real_dsi):
    ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.0003,
             f'DSI={val:.4f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
ax2.set_ylabel('Decoupled Stress Index (DSI)', fontsize=9)
ax2.set_title('Real Decoupled Stress Index (DSI) by Crop', fontsize=9.5, fontweight='bold')
ax2.axhline(y=np.mean(real_dsi), color='#2c3e50', linestyle='--', lw=1.5,
            label=f'Mean DSI={np.mean(real_dsi):.4f}')
ax2.legend(fontsize=8)
ax2.grid(axis='y', alpha=0.3)
ax2.set_facecolor('#f8f9fa')
ax2.set_ylim(0, max(real_dsi)*1.4 + 0.001)
fig.suptitle('Figure 3: Real DSI Values Computed from Actual Telemetry Data', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{FIGURES_DIR}/fig3_dsi_barchart.png", dpi=200, bbox_inches='tight')
plt.savefig(f"{FIGURES_DIR}/fig3_dsi_barchart.pdf", dpi=200, bbox_inches='tight')
plt.close()
print("Figure 3 done.")

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 4: VPD logistic regression (Corn only) + daily DSI timeseries
# ═══════════════════════════════════════════════════════════════════════════
print("Generating Figure 4 (real data)...")
fig, (ax_lr, ax_ts) = plt.subplots(1, 2, figsize=(14, 5))

# Left: logistic regression (Corn only - only crop with decoupled events)
sub_c = df[df['crop']=='Corn'].copy()
sub_c['is_decoupled'] = (sub_c['stress_class']=='Decoupled Atmospheric Stress').astype(int)
vpd_bins = np.arange(0, sub_c['VPD'].max()+0.2, 0.2)
vpd_means, prob_means, prob_se = [], [], []
for i in range(len(vpd_bins)-1):
    mask = (sub_c['VPD'] >= vpd_bins[i]) & (sub_c['VPD'] < vpd_bins[i+1])
    if mask.sum() > 20:
        p = sub_c.loc[mask,'is_decoupled'].mean()
        vpd_means.append((vpd_bins[i]+vpd_bins[i+1])/2)
        prob_means.append(p)
        prob_se.append(np.sqrt(p*(1-p)/mask.sum()))
ax_lr.errorbar(vpd_means, prob_means, yerr=prob_se, fmt='o', color='#e67e22',
               markersize=6, capsize=3, lw=1.5, elinewidth=1, label='Corn (empirical bins)')
vpd_range = np.linspace(0, sub_c['VPD'].max(), 300)
prob_fit = clf_corn.predict_proba(vpd_range.reshape(-1,1))[:,1]
ax_lr.plot(vpd_range, prob_fit, color='#e67e22', lw=2.5, alpha=0.9,
           label=f'Corn logistic fit (β={beta_corn:.3f}, AUC={auc_corn:.3f})')
ax_lr.axhline(y=0.5, color='gray', linestyle=':', lw=1.2, alpha=0.6)
ax_lr.set_xlabel('Vapor Pressure Deficit (kPa)', fontsize=10)
ax_lr.set_ylabel('P(Decoupled Atmospheric Stress)', fontsize=10)
ax_lr.set_title('VPD → Decoupled Stress Probability\n(Corn only; Alfalfa & Tomato: DSI=0)', fontsize=9.5, fontweight='bold')
ax_lr.legend(fontsize=8)
ax_lr.set_ylim(0, 0.15)
ax_lr.grid(alpha=0.3)
ax_lr.set_facecolor('#f8f9fa')

# Right: daily DSI + VPD timeseries
ax_twin = ax_ts.twinx()
ax_ts.bar(range(len(daily_df)), daily_df['DSI'], color='#f39c12', alpha=0.75, label='Daily DSI')
ax_twin.plot(range(len(daily_df)), daily_df['VPD'], color='#e74c3c', lw=2, marker='o', markersize=4, label='Mean VPD')
ax_ts.set_xticks(range(0, len(daily_df), 3))
ax_ts.set_xticklabels([str(daily_df['date'].iloc[i]) for i in range(0, len(daily_df), 3)],
                       rotation=35, fontsize=7)
ax_ts.set_ylabel('Daily DSI', fontsize=9, color='#f39c12')
ax_twin.set_ylabel('Mean VPD (kPa)', fontsize=9, color='#e74c3c')
ax_ts.set_title(f'Daily DSI vs VPD (r={r_val:.3f}, p={p_r:.4f})\n21-day Pilot Period', fontsize=9.5, fontweight='bold')
lines1, labels1 = ax_ts.get_legend_handles_labels()
lines2, labels2 = ax_twin.get_legend_handles_labels()
ax_ts.legend(lines1+lines2, labels1+labels2, fontsize=8, loc='upper left')
ax_ts.grid(axis='y', alpha=0.3)
ax_ts.set_facecolor('#f8f9fa')

fig.suptitle('Figure 4: Real Logistic Regression and Temporal DSI Dynamics', fontsize=11, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{FIGURES_DIR}/fig4_vpd_logistic.png", dpi=200, bbox_inches='tight')
plt.savefig(f"{FIGURES_DIR}/fig4_vpd_logistic.pdf", dpi=200, bbox_inches='tight')
plt.close()
print("Figure 4 done.")

# ═══════════════════════════════════════════════════════════════════════════
# FIGURE 5: Spatial heatmap – real sector DSI
# ═══════════════════════════════════════════════════════════════════════════
print("Generating Figure 5 (real data)...")
cmap_custom = LinearSegmentedColormap.from_list('dsi_cmap',
    ['#2ecc71','#f1c40f','#e67e22','#c0392b'], N=256)
fig, axes = plt.subplots(1, 3, figsize=(15, 5))
max_dsi = 0
grid_all = {}
for field, crop in [('Field-A (Corn)','Corn'),('Field-B (Alfalfa)','Alfalfa'),('Field-D (Tomato)','Tomato')]:
    sub = df[df['field_name']==field]
    grid = np.zeros((8,8))
    for r_ in range(8):
        for c_ in range(8):
            cell = sub[(sub['sector_row']==r_) & (sub['sector_col']==c_)]
            if len(cell)>0:
                stress = cell[cell['stress_class']!='No Stress']
                dec = cell[cell['stress_class']=='Decoupled Atmospheric Stress']
                grid[r_,c_] = len(dec)/len(stress) if len(stress)>0 else 0
    grid_all[crop] = grid
    max_dsi = max(max_dsi, grid.max())

vmax = max(max_dsi, 0.001)
for ax, crop in zip(axes, ['Corn','Alfalfa','Tomato']):
    grid = grid_all[crop]
    im = ax.imshow(grid, cmap=cmap_custom, vmin=0, vmax=vmax, aspect='auto')
    ax.set_title(crop, fontsize=10, fontweight='bold')
    ax.set_xlabel('Sector Column', fontsize=9)
    ax.set_ylabel('Sector Row', fontsize=9)
    ax.set_xticks(range(8)); ax.set_yticks(range(8))
    for r_ in range(8):
        for c_ in range(8):
            val = grid[r_,c_]
            text_color = 'white' if val > vmax*0.6 else '#2c3e50'
            ax.text(c_, r_, f'{val:.4f}', ha='center', va='center',
                    fontsize=5.5, color=text_color, fontweight='bold')
    plt.colorbar(im, ax=ax, label='DSI', fraction=0.046, pad=0.04)

fig.suptitle('Figure 5: Real Spatial DSI Distribution Across 8×8 Sector Grids\n'
             '(Green=low DSI; Red=high DSI. Corn: max DSI observed; Alfalfa & Tomato: DSI=0 throughout)',
             fontsize=10, fontweight='bold')
plt.tight_layout()
plt.savefig(f"{FIGURES_DIR}/fig5_spatial_dsi.png", dpi=200, bbox_inches='tight')
plt.savefig(f"{FIGURES_DIR}/fig5_spatial_dsi.pdf", dpi=200, bbox_inches='tight')
plt.close()
print("Figure 5 done.")

print("\n[OK] All real statistics computed. All figures regenerated from real data.")
print("Summary saved to real_stats.json")
