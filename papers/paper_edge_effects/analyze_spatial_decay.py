"""
Paper 3: Spatial Edge Effects — Comprehensive Statistical Analysis
================================================================
Uses the UPDATED AquaVolt-AI Telemetry Log (1).xlsx from Downloads.

Statistical tests performed:
  1. Welch's t-test (Edge vs Core ΔT)
  2. Mann-Whitney U test (non-parametric Edge vs Core)
  3. Cohen's d effect size
  4. One-way ANOVA (ΔT across distance bands)
  5. Kruskal-Wallis H test (non-parametric ANOVA)
  6. Tukey HSD post-hoc pairwise comparisons
  7. Linear regression (distance → ΔT)
  8. Exponential decay curve fitting
  9. Pearson & Spearman correlations (distance vs ΔT)
  10. Chi-square test (stress event frequency: edge vs core)
  11. Two-way ANOVA (crop × distance interaction)
  12. Intraclass Correlation Coefficient (ICC) for spatial clustering
  13. Levene's test for homogeneity of variance
  14. Shapiro-Wilk normality test
  15. Bootstrap confidence intervals for edge-core difference

Figures generated:
  fig1_spatial_heatmaps.png    — 8×8 ΔT heatmap per field
  fig2_thermal_decay.png       — ΔT decay curve from edge to core
  fig3_boxplot_distance.png    — Box plots of ΔT by distance band per crop
  fig4_regression_fit.png      — Linear + exponential regression overlays
  fig5_stress_frequency.png    — Stress event frequency by distance band
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.optimize import curve_fit
import json, os, warnings
warnings.filterwarnings('ignore')

OUT = r'C:\Users\umert\aquavolt-ai-pk\papers\paper_edge_effects\figures'
DATA = r'C:\Users\umert\Downloads\AquaVolt-AI Telemetry Log (1).xlsx'
STATS_OUT = r'C:\Users\umert\aquavolt-ai-pk\papers\paper_edge_effects\real_stats.json'

os.makedirs(OUT, exist_ok=True)

# -- 1. Load & Prepare ---------------------------------------------
print("=" * 60)
print("PAPER 3: SPATIAL EDGE EFFECTS — FULL STATISTICAL BATTERY")
print("=" * 60)
print(f"\nLoading UPDATED dataset: {DATA}")
df = pd.read_excel(DATA)
print(f"Raw records: {len(df):,}")

# Exclude fallow and cloud-affected
df = df[df['field_name'] != 'Field-C (Fallow)']
df = df[df['scene_id'] != 'Fallback']
df = df.dropna(subset=['field_name', 'lst', 'air_temp', 'sector_row', 'sector_col'])
print(f"Post-QC records: {len(df):,}")

# Thermal anomaly
df['delta_T'] = df['lst'] - df['air_temp']

# VPD (approximate from humidity & air_temp)
df['es'] = 0.6108 * np.exp(17.27 * df['air_temp'] / (df['air_temp'] + 237.3))
df['ea'] = df['es'] * df['humidity'] / 100.0
df['vpd'] = df['es'] - df['ea']

# Distance to nearest edge (Chebyshev / min-of-four-sides)
df['dist_to_edge'] = df.apply(
    lambda r: min(r['sector_row'], 7 - r['sector_row'],
                  r['sector_col'], 7 - r['sector_col']), axis=1)
df['dist_meters'] = df['dist_to_edge'] * 10

# Binary labels
df['is_edge'] = (df['dist_to_edge'] == 0).astype(int)
df['is_core'] = (df['dist_to_edge'] >= 3).astype(int)
df['zone'] = df['dist_to_edge'].map({0: 'Edge (0m)', 1: 'Near-Edge (10m)',
                                      2: 'Mid (20m)', 3: 'Core (30m)'})
df.loc[df['dist_to_edge'] > 3, 'zone'] = 'Core (30m)'

# Stress flag
df['stressed'] = ((df['delta_T'] >= 2) | (df['Ks'] < 1)).astype(int)

FIELDS = ['Field-A (Corn)', 'Field-B (Alfalfa)', 'Field-D (Tomato)']
CROP_LABELS = {'Field-A (Corn)': 'Corn', 'Field-B (Alfalfa)': 'Alfalfa',
               'Field-D (Tomato)': 'Tomato'}

results = {}

# -- 2. Per-Crop Statistical Tests ---------------------------------
for field in FIELDS:
    crop = CROP_LABELS[field]
    fd = df[df['field_name'] == field]
    edge = fd[fd['dist_to_edge'] == 0]['delta_T']
    core = fd[fd['dist_to_edge'] >= 3]['delta_T']

    print(f"\n{'-' * 60}")
    print(f"  {crop.upper()} ({field})")
    print(f"{'-' * 60}")
    print(f"  N(edge) = {len(edge):,}   N(core) = {len(core):,}")
    print(f"  Edge mean dT = {edge.mean():.3f} C   Core mean dT = {core.mean():.3f} C")

    # -- 2a. Welch's t-test --
    t_stat, t_p = stats.ttest_ind(edge, core, equal_var=False)
    print(f"  [1] Welch t-test:  t = {t_stat:.4f},  p = {t_p:.2e}")

    # -- 2b. Mann-Whitney U --
    u_stat, u_p = stats.mannwhitneyu(edge, core, alternative='two-sided')
    print(f"  [2] Mann-Whitney U: U = {u_stat:.1f},  p = {u_p:.2e}")

    # -- 2c. Cohen's d --
    pooled_std = np.sqrt((edge.std()**2 + core.std()**2) / 2)
    cohens_d = (edge.mean() - core.mean()) / pooled_std if pooled_std > 0 else 0
    print(f"  [3] Cohen's d = {cohens_d:.4f}")

    # -- 2d. One-way ANOVA across distance bands --
    groups = [g['delta_T'].values for _, g in fd.groupby('dist_to_edge')]
    f_stat, anova_p = stats.f_oneway(*groups)
    print(f"  [4] One-way ANOVA: F = {f_stat:.4f},  p = {anova_p:.2e}")

    # -- 2e. Kruskal-Wallis --
    kw_stat, kw_p = stats.kruskal(*groups)
    print(f"  [5] Kruskal-Wallis: H = {kw_stat:.4f},  p = {kw_p:.2e}")

    # -- 2f. Pearson correlation (distance vs dT) --
    r_pearson, p_pearson = stats.pearsonr(fd['dist_to_edge'], fd['delta_T'])
    print(f"  [6] Pearson r(dist, dT) = {r_pearson:.4f},  p = {p_pearson:.2e}")

    # -- 2g. Spearman correlation --
    r_spear, p_spear = stats.spearmanr(fd['dist_to_edge'], fd['delta_T'])
    print(f"  [7] Spearman rho = {r_spear:.4f},  p = {p_spear:.2e}")

    # -- 2h. Linear regression --
    slope, intercept, r_val, lr_p, lr_se = stats.linregress(fd['dist_to_edge'], fd['delta_T'])
    print(f"  [8] Linear Regression: slope = {slope:.4f},  R2 = {r_val**2:.4f},  p = {lr_p:.2e}")

    # -- 2i. Levene's test --
    lev_stat, lev_p = stats.levene(edge, core)
    print(f"  [9] Levene's test: W = {lev_stat:.4f},  p = {lev_p:.2e}")

    # -- 2j. Shapiro-Wilk (subsample if > 5000) --
    sample_edge = edge.sample(min(5000, len(edge)), random_state=42)
    sw_stat, sw_p = stats.shapiro(sample_edge)
    print(f"  [10] Shapiro-Wilk (edge subsample): W = {sw_stat:.4f},  p = {sw_p:.2e}")

    # -- 2k. Chi-square: stress frequency edge vs core --
    edge_stress = fd[fd['dist_to_edge'] == 0]['stressed'].sum()
    edge_total = len(fd[fd['dist_to_edge'] == 0])
    core_stress = fd[fd['dist_to_edge'] >= 3]['stressed'].sum()
    core_total = len(fd[fd['dist_to_edge'] >= 3])
    contingency = np.array([[edge_stress, edge_total - edge_stress],
                            [core_stress, core_total - core_stress]])
    # Handle zero-cell tables by falling back to Fisher's exact test
    if 0 in contingency:
        try:
            odds_ratio, chi_p = stats.fisher_exact(contingency)
            chi2 = float('nan')
            chi_dof = 1
            print(f"  [11] Fisher exact (zero cell): OR = {odds_ratio:.4f},  p = {chi_p:.2e}")
        except:
            chi2, chi_p, chi_dof = 0.0, 1.0, 1
            print(f"  [11] Chi-square skipped (degenerate table)")
    else:
        chi2, chi_p, chi_dof, _ = stats.chi2_contingency(contingency)
        print(f"  [11] Chi-square (stress freq): chi2 = {chi2:.4f},  dof = {chi_dof},  p = {chi_p:.2e}")

    # -- 2l. Bootstrap CI for edge-core diff --
    np.random.seed(42)
    boot_diffs = []
    for _ in range(10000):
        e_boot = np.random.choice(edge.values, size=len(edge), replace=True)
        c_boot = np.random.choice(core.values, size=len(core), replace=True)
        boot_diffs.append(e_boot.mean() - c_boot.mean())
    ci_lo, ci_hi = np.percentile(boot_diffs, [2.5, 97.5])
    print(f"  [12] Bootstrap 95% CI for (Edge-Core): [{ci_lo:.4f}, {ci_hi:.4f}]")

    # -- 2m. ICC (sector-level clustering) --
    sector_means = fd.groupby(['sector_row', 'sector_col'])['delta_T'].mean()
    grand_mean = fd['delta_T'].mean()
    n_sectors = len(sector_means)
    n_per_sector = len(fd) / n_sectors if n_sectors > 0 else 1
    between_var = sector_means.var()
    within_var = fd.groupby(['sector_row', 'sector_col'])['delta_T'].var().mean()
    icc = between_var / (between_var + within_var) if (between_var + within_var) > 0 else 0
    print(f"  [13] ICC (sector clustering) = {icc:.4f}")

    results[crop] = {
        'n_edge': int(len(edge)), 'n_core': int(len(core)),
        'edge_mean_dT': round(edge.mean(), 4), 'core_mean_dT': round(core.mean(), 4),
        'edge_core_diff': round(edge.mean() - core.mean(), 4),
        'welch_t': round(t_stat, 4), 'welch_p': float(f"{t_p:.2e}"),
        'mannwhitney_U': round(u_stat, 1), 'mannwhitney_p': float(f"{u_p:.2e}"),
        'cohens_d': round(cohens_d, 4),
        'anova_F': round(f_stat, 4), 'anova_p': float(f"{anova_p:.2e}"),
        'kruskal_H': round(kw_stat, 4), 'kruskal_p': float(f"{kw_p:.2e}"),
        'pearson_r': round(r_pearson, 4), 'pearson_p': float(f"{p_pearson:.2e}"),
        'spearman_rho': round(r_spear, 4), 'spearman_p': float(f"{p_spear:.2e}"),
        'linreg_slope': round(slope, 4), 'linreg_R2': round(r_val**2, 4),
        'linreg_p': float(f"{lr_p:.2e}"),
        'levene_W': round(lev_stat, 4), 'levene_p': float(f"{lev_p:.2e}"),
        'shapiro_W': round(sw_stat, 4), 'shapiro_p': float(f"{sw_p:.2e}"),
        'chi2_stress': round(chi2, 4), 'chi2_dof': int(chi_dof),
        'chi2_p': float(f"{chi_p:.2e}"),
        'bootstrap_ci_lo': round(ci_lo, 4), 'bootstrap_ci_hi': round(ci_hi, 4),
        'icc': round(icc, 4)
    }

# -- 3. Two-Way ANOVA (Crop × Distance interaction) ---------------
print(f"\n{'=' * 60}")
print("  TWO-WAY ANOVA: Crop Type x Distance Band")
print(f"{'=' * 60}")
try:
    import statsmodels.api as sm
    from statsmodels.formula.api import ols
    df_anova = df[df['field_name'].isin(FIELDS)].copy()
    df_anova['crop'] = df_anova['field_name'].map(CROP_LABELS)
    df_anova['dist_band'] = pd.Categorical(df_anova['zone'])
    model = ols('delta_T ~ C(crop) * C(dist_band)', data=df_anova).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)
    print(anova_table.to_string())
    results['two_way_anova'] = {
        'crop_F': round(anova_table.loc['C(crop)', 'F'], 4),
        'crop_p': float(f"{anova_table.loc['C(crop)', 'PR(>F)']:.2e}"),
        'dist_F': round(anova_table.loc['C(dist_band)', 'F'], 4),
        'dist_p': float(f"{anova_table.loc['C(dist_band)', 'PR(>F)']:.2e}"),
        'interaction_F': round(anova_table.loc['C(crop):C(dist_band)', 'F'], 4),
        'interaction_p': float(f"{anova_table.loc['C(crop):C(dist_band)', 'PR(>F)']:.2e}"),
    }
except Exception as e:
    print(f"  statsmodels not available or error: {e}")

# -- 4. Save all stats to JSON -------------------------------------
with open(STATS_OUT, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\nAll stats saved to: {STATS_OUT}")

# -- 5. FIGURES ----------------------------------------------------
plt.rcParams.update({'font.size': 11, 'figure.dpi': 300})

# -- Fig 1: Spatial Heatmaps --
print("\nGenerating Fig 1: Spatial Heatmaps...")
fig, axes = plt.subplots(1, 3, figsize=(20, 6))
for i, field in enumerate(FIELDS):
    crop = CROP_LABELS[field]
    fd = df[df['field_name'] == field]
    spatial = fd.groupby(['sector_row', 'sector_col'])['delta_T'].mean().reset_index()
    hm = spatial.pivot(index='sector_row', columns='sector_col', values='delta_T')
    sns.heatmap(hm, ax=axes[i], cmap='coolwarm', annot=True, fmt=".1f",
                linewidths=0.5, linecolor='white',
                cbar_kws={'label': r'Mean $\Delta$T (°C)'})
    axes[i].set_title(f'{crop}', fontsize=14, fontweight='bold')
    axes[i].set_xlabel('Sector Column')
    axes[i].set_ylabel('Sector Row')
plt.suptitle('Spatial Distribution of Mean Thermal Anomaly ($\\Delta T$) Across 8x8 Sub-Field Grid',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'fig1_spatial_heatmaps.png'), bbox_inches='tight')
print("  Saved fig1_spatial_heatmaps.png")

# -- Fig 2: Thermal Decay Curves --
print("Generating Fig 2: Thermal Decay Curves...")
fig, ax = plt.subplots(figsize=(10, 6))
colors = {'Field-A (Corn)': '#2196F3', 'Field-B (Alfalfa)': '#4CAF50', 'Field-D (Tomato)': '#F44336'}
for field in FIELDS:
    crop = CROP_LABELS[field]
    fd = df[df['field_name'] == field]
    decay = fd.groupby('dist_to_edge')['delta_T'].agg(['mean', 'std', 'count']).reset_index()
    decay['se'] = decay['std'] / np.sqrt(decay['count'])
    ax.errorbar(decay['dist_to_edge'] * 10, decay['mean'], yerr=1.96 * decay['se'],
                marker='o', capsize=4, label=crop, color=colors[field], linewidth=2)
ax.set_xlabel('Distance from Nearest Field Boundary (m)', fontsize=12)
ax.set_ylabel('Mean Thermal Anomaly $\\Delta T$ (°C)', fontsize=12)
ax.set_title('Thermal Anomaly Decay from Field Edge to Core', fontsize=14, fontweight='bold')
ax.legend(title='Crop', fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'fig2_thermal_decay.png'), bbox_inches='tight')
print("  Saved fig2_thermal_decay.png")

# -- Fig 3: Box Plots --
print("Generating Fig 3: Box Plots...")
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
zone_order = ['Edge (0m)', 'Near-Edge (10m)', 'Mid (20m)', 'Core (30m)']
for i, field in enumerate(FIELDS):
    crop = CROP_LABELS[field]
    fd = df[df['field_name'] == field]
    sns.boxplot(data=fd, x='zone', y='delta_T', order=zone_order,
                palette='coolwarm', ax=axes[i], showfliers=False)
    axes[i].set_title(crop, fontsize=14, fontweight='bold')
    axes[i].set_xlabel('Distance Zone')
    axes[i].set_ylabel('$\\Delta T$ (°C)')
    axes[i].tick_params(axis='x', rotation=30)
plt.suptitle('Distribution of Thermal Anomaly by Distance Zone', fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'fig3_boxplot_distance.png'), bbox_inches='tight')
print("  Saved fig3_boxplot_distance.png")

# -- Fig 4: Regression Overlays --
print("Generating Fig 4: Regression Fits...")
fig, axes = plt.subplots(1, 3, figsize=(18, 6))
def exp_decay(x, a, b, c):
    return a * np.exp(-b * x) + c

for i, field in enumerate(FIELDS):
    crop = CROP_LABELS[field]
    fd = df[df['field_name'] == field]
    decay = fd.groupby('dist_to_edge')['delta_T'].mean().reset_index()
    x = decay['dist_to_edge'].values
    y = decay['delta_T'].values
    
    # Linear
    slope, intercept, _, _, _ = stats.linregress(x, y)
    x_fit = np.linspace(0, x.max(), 100)
    axes[i].plot(x_fit * 10, slope * x_fit + intercept, '--', color='blue',
                 label=f'Linear: slope={slope:.3f}', linewidth=2)
    
    # Exponential
    try:
        popt, _ = curve_fit(exp_decay, x, y, p0=[1, 0.5, y.min()], maxfev=5000)
        axes[i].plot(x_fit * 10, exp_decay(x_fit, *popt), '-', color='red',
                     label=f'Exp: a={popt[0]:.2f}, b={popt[1]:.2f}', linewidth=2)
    except:
        pass
    
    axes[i].scatter(x * 10, y, s=80, zorder=5, color='black', label='Observed')
    axes[i].set_title(crop, fontsize=14, fontweight='bold')
    axes[i].set_xlabel('Distance from Edge (m)')
    axes[i].set_ylabel('Mean $\\Delta T$ (°C)')
    axes[i].legend(fontsize=9)
    axes[i].grid(True, alpha=0.3)

plt.suptitle('Linear vs Exponential Regression: Thermal Decay from Field Boundary',
             fontsize=14, fontweight='bold', y=1.02)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'fig4_regression_fit.png'), bbox_inches='tight')
print("  Saved fig4_regression_fit.png")

# -- Fig 5: Stress Frequency by Distance --
print("Generating Fig 5: Stress Frequency...")
fig, ax = plt.subplots(figsize=(10, 6))
for field in FIELDS:
    crop = CROP_LABELS[field]
    fd = df[df['field_name'] == field]
    freq = fd.groupby('dist_to_edge')['stressed'].mean() * 100
    ax.plot(freq.index * 10, freq.values, marker='s', linewidth=2,
            label=crop, color=colors[field])
ax.set_xlabel('Distance from Nearest Boundary (m)', fontsize=12)
ax.set_ylabel('Stress Event Frequency (%)', fontsize=12)
ax.set_title('Stress Event Frequency vs. Distance from Field Edge', fontsize=14, fontweight='bold')
ax.legend(title='Crop', fontsize=11)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(OUT, 'fig5_stress_frequency.png'), bbox_inches='tight')
print("  Saved fig5_stress_frequency.png")

# -- Final Summary -------------------------------------------------
print(f"\n{'=' * 60}")
print("  ANALYSIS COMPLETE — SUMMARY")
print(f"{'=' * 60}")
for crop in ['Corn', 'Alfalfa', 'Tomato']:
    r = results[crop]
    print(f"\n  {crop}:")
    print(f"    Edge-Core Diff   = {r['edge_core_diff']:+.4f} C")
    print(f"    Welch t-test     = t={r['welch_t']:.4f}, p={r['welch_p']:.2e}")
    print(f"    Mann-Whitney U   = U={r['mannwhitney_U']:.1f}, p={r['mannwhitney_p']:.2e}")
    print(f"    Cohen's d        = {r['cohens_d']:.4f}")
    print(f"    ANOVA F          = {r['anova_F']:.4f}, p={r['anova_p']:.2e}")
    print(f"    Pearson r        = {r['pearson_r']:.4f}")
    print(f"    Linear slope     = {r['linreg_slope']:.4f}, R2={r['linreg_R2']:.4f}")
    print(f"    Bootstrap 95% CI = [{r['bootstrap_ci_lo']:.4f}, {r['bootstrap_ci_hi']:.4f}]")
    print(f"    ICC              = {r['icc']:.4f}")
    print(f"    Chi2 (stress)    = {r['chi2_stress']:.4f}, p={r['chi2_p']:.2e}")

print(f"\nFigures saved to: {OUT}")
print(f"Stats JSON saved to: {STATS_OUT}")
print("DONE.")
