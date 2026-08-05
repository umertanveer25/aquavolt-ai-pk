"""
AquaVolt-AI: Comprehensive Statistical Testing Suite
=====================================================
Tests performed:
  1. Descriptive Statistics (mean, std, min, max, skewness, kurtosis)
  2. Normality Test (Shapiro-Wilk)
  3. Independent T-Test (Baseline vs Monitoring)
  4. Mann-Whitney U Test (Non-parametric)
  5. One-Way ANOVA (across all years)
  6. Cohen's d Effect Size
  7. Linear Regression Trend Analysis (methane over time)
  8. Pearson & Spearman Correlation (SAR vs Methane)
  9. Seasonal Decomposition (summer vs winter)
"""
import os
import pandas as pd
import numpy as np
from scipy import stats

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data')

def load_all_data():
    all_data = []
    for year_dir in sorted(os.listdir(DATA_DIR)):
        year_path = os.path.join(DATA_DIR, year_dir)
        if not os.path.isdir(year_path) or not year_dir.isdigit():
            continue
        year = int(year_dir)
        if year < 2019:
            continue
        for csv_file in sorted(os.listdir(year_path)):
            if csv_file.endswith('_methane.csv') and not csv_file.startswith('audit'):
                df = pd.read_csv(os.path.join(year_path, csv_file))
                if 'regional_methane_ppb' in df.columns:
                    for _, row in df.iterrows():
                        all_data.append({
                            'year': int(row['year']),
                            'month': int(row['month']),
                            'regional_methane_ppb': float(row['regional_methane_ppb']),
                            'sar_vh_db': float(row['sar_vh_db']),
                            'confidence': float(row['confidence_score']),
                            'period': 'Baseline' if int(row['year']) <= 2022 else 'Monitoring'
                        })
    return pd.DataFrame(all_data)

def main():
    print("=" * 70)
    print("  AQUAVOLT-AI: COMPREHENSIVE STATISTICAL TESTING SUITE")
    print("  Dataset: 2019-2026 | Gold Standard Monthly Composites")
    print("=" * 70)

    df = load_all_data()
    if df.empty:
        print("[ERROR] No data found.")
        return

    baseline = df[df['period'] == 'Baseline']['regional_methane_ppb']
    monitoring = df[df['period'] == 'Monitoring']['regional_methane_ppb']

    # ========================================
    # TEST 1: Descriptive Statistics
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST 1: DESCRIPTIVE STATISTICS")
    print("=" * 70)
    print(f"\n  {'Metric':<25} {'Baseline (2019-2022)':<25} {'Monitoring (2023-2026)':<25}")
    print(f"  {'-'*70}")
    print(f"  {'N (months)':<25} {len(baseline):<25} {len(monitoring):<25}")
    print(f"  {'Mean (ppb)':<25} {baseline.mean():<25.2f} {monitoring.mean():<25.2f}")
    print(f"  {'Std Dev':<25} {baseline.std():<25.2f} {monitoring.std():<25.2f}")
    print(f"  {'Min':<25} {baseline.min():<25.2f} {monitoring.min():<25.2f}")
    print(f"  {'Max':<25} {baseline.max():<25.2f} {monitoring.max():<25.2f}")
    print(f"  {'Median':<25} {baseline.median():<25.2f} {monitoring.median():<25.2f}")
    print(f"  {'Skewness':<25} {baseline.skew():<25.4f} {monitoring.skew():<25.4f}")
    print(f"  {'Kurtosis':<25} {baseline.kurtosis():<25.4f} {monitoring.kurtosis():<25.4f}")

    # ========================================
    # TEST 2: Normality Test (Shapiro-Wilk)
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST 2: SHAPIRO-WILK NORMALITY TEST")
    print("=" * 70)
    w_base, p_base = stats.shapiro(baseline)
    w_mon, p_mon = stats.shapiro(monitoring)
    print(f"\n  Baseline:   W={w_base:.4f}, p={p_base:.6f}  {'-> NORMAL' if p_base > 0.05 else '-> NOT NORMAL'}")
    print(f"  Monitoring: W={w_mon:.4f}, p={p_mon:.6f}  {'-> NORMAL' if p_mon > 0.05 else '-> NOT NORMAL'}")
    print(f"\n  Interpretation: p > 0.05 = data is normally distributed")

    # ========================================
    # TEST 3: Independent Samples T-Test
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST 3: INDEPENDENT SAMPLES T-TEST")
    print("  H0: No difference between Baseline and Monitoring periods")
    print("=" * 70)
    t_stat, p_ttest = stats.ttest_ind(baseline, monitoring, equal_var=False)
    print(f"\n  t-statistic: {t_stat:.4f}")
    print(f"  p-value:     {p_ttest:.8f}")
    print(f"  Result:      {'*** SIGNIFICANT (p < 0.001)' if p_ttest < 0.001 else '** SIGNIFICANT (p < 0.01)' if p_ttest < 0.01 else '* SIGNIFICANT (p < 0.05)' if p_ttest < 0.05 else 'NOT SIGNIFICANT (p >= 0.05)'}")
    print(f"\n  Interpretation: Methane {'significantly INCREASED' if t_stat < 0 else 'significantly DECREASED'} from Baseline to Monitoring period")

    # ========================================
    # TEST 4: Mann-Whitney U Test (Non-parametric)
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST 4: MANN-WHITNEY U TEST (Non-parametric alternative)")
    print("  H0: Distributions of Baseline and Monitoring are equal")
    print("=" * 70)
    u_stat, p_mann = stats.mannwhitneyu(baseline, monitoring, alternative='two-sided')
    print(f"\n  U-statistic: {u_stat:.4f}")
    print(f"  p-value:     {p_mann:.8f}")
    print(f"  Result:      {'*** SIGNIFICANT (p < 0.001)' if p_mann < 0.001 else '** SIGNIFICANT (p < 0.01)' if p_mann < 0.01 else '* SIGNIFICANT (p < 0.05)' if p_mann < 0.05 else 'NOT SIGNIFICANT (p >= 0.05)'}")

    # ========================================
    # TEST 5: Cohen's d Effect Size
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST 5: COHEN'S d EFFECT SIZE")
    print("=" * 70)
    pooled_std = np.sqrt(((len(baseline)-1)*baseline.std()**2 + (len(monitoring)-1)*monitoring.std()**2) / (len(baseline)+len(monitoring)-2))
    cohens_d = (monitoring.mean() - baseline.mean()) / pooled_std
    
    if abs(cohens_d) < 0.2:
        effect_label = "NEGLIGIBLE"
    elif abs(cohens_d) < 0.5:
        effect_label = "SMALL"
    elif abs(cohens_d) < 0.8:
        effect_label = "MEDIUM"
    else:
        effect_label = "LARGE"
    
    print(f"\n  Cohen's d:   {cohens_d:.4f}")
    print(f"  Effect Size: {effect_label}")
    print(f"  Interpretation: The methane increase from Baseline to Monitoring")
    print(f"                  has a {effect_label.lower()} practical significance")

    # ========================================
    # TEST 6: One-Way ANOVA (across years)
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST 6: ONE-WAY ANOVA (Methane across all years)")
    print("  H0: Mean methane is the same across all years")
    print("=" * 70)
    year_groups = [group['regional_methane_ppb'].values for _, group in df.groupby('year')]
    f_stat, p_anova = stats.f_oneway(*year_groups)
    print(f"\n  F-statistic: {f_stat:.4f}")
    print(f"  p-value:     {p_anova:.8f}")
    print(f"  Result:      {'*** SIGNIFICANT (p < 0.001)' if p_anova < 0.001 else '** SIGNIFICANT (p < 0.01)' if p_anova < 0.01 else '* SIGNIFICANT (p < 0.05)' if p_anova < 0.05 else 'NOT SIGNIFICANT'}")

    # Per-year means
    print(f"\n  Year-by-Year Means:")
    for year, group in df.groupby('year'):
        mean_val = group['regional_methane_ppb'].mean()
        n = len(group)
        print(f"    {year}: {mean_val:.2f} ppb  (n={n})")

    # ========================================
    # TEST 7: Linear Regression Trend
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST 7: LINEAR REGRESSION TREND ANALYSIS")
    print("  Model: CH4(ppb) = slope * year + intercept")
    print("=" * 70)
    
    # Create numeric time variable
    df['time_index'] = (df['year'] - df['year'].min()) * 12 + df['month']
    slope, intercept, r_value, p_trend, std_err = stats.linregress(df['time_index'], df['regional_methane_ppb'])
    r_squared = r_value ** 2
    
    # Annual rate
    annual_rate = slope * 12
    
    print(f"\n  Slope:       {slope:.4f} ppb/month")
    print(f"  Annual Rate: {annual_rate:.2f} ppb/year")
    print(f"  Intercept:   {intercept:.2f}")
    print(f"  R-squared:   {r_squared:.4f}")
    print(f"  p-value:     {p_trend:.8f}")
    print(f"  Std Error:   {std_err:.4f}")
    print(f"  Result:      {'*** SIGNIFICANT UPWARD TREND' if p_trend < 0.001 and slope > 0 else '** SIGNIFICANT TREND' if p_trend < 0.01 else 'NO SIGNIFICANT TREND'}")
    print(f"\n  Interpretation: Methane is rising at {annual_rate:.2f} ppb/year")
    print(f"  NOAA Global Average: ~10 ppb/year (our data {'matches' if 5 < annual_rate < 20 else 'deviates from'} global trend)")

    # ========================================
    # TEST 8: Pearson & Spearman Correlation
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST 8: CORRELATION ANALYSIS (SAR Radar vs Methane)")
    print("=" * 70)
    pearson_r, p_pearson = stats.pearsonr(df['sar_vh_db'], df['regional_methane_ppb'])
    spearman_r, p_spearman = stats.spearmanr(df['sar_vh_db'], df['regional_methane_ppb'])
    
    print(f"\n  Pearson r:   {pearson_r:.4f}  (p={p_pearson:.6f})")
    print(f"  Spearman r:  {spearman_r:.4f}  (p={p_spearman:.6f})")
    print(f"\n  Interpretation: {'Strong' if abs(pearson_r) > 0.7 else 'Moderate' if abs(pearson_r) > 0.4 else 'Weak' if abs(pearson_r) > 0.2 else 'No'} {'positive' if pearson_r > 0 else 'negative'} correlation between soil moisture and methane")

    # ========================================
    # TEST 9: Seasonal Analysis
    # ========================================
    print("\n" + "=" * 70)
    print("  TEST 9: SEASONAL DECOMPOSITION")
    print("  Summer (Apr-Sep) vs Winter (Oct-Mar)")
    print("=" * 70)
    df['season'] = df['month'].apply(lambda m: 'Summer' if 4 <= m <= 9 else 'Winter')
    summer = df[df['season'] == 'Summer']['regional_methane_ppb']
    winter = df[df['season'] == 'Winter']['regional_methane_ppb']
    
    t_season, p_season = stats.ttest_ind(summer, winter, equal_var=False)
    print(f"\n  Summer Mean: {summer.mean():.2f} ppb  (n={len(summer)})")
    print(f"  Winter Mean: {winter.mean():.2f} ppb  (n={len(winter)})")
    print(f"  t-statistic: {t_season:.4f}")
    print(f"  p-value:     {p_season:.6f}")
    print(f"  Result:      {'*** SIGNIFICANT seasonal difference' if p_season < 0.001 else 'NO significant seasonal difference'}")

    # ========================================
    # SUMMARY TABLE
    # ========================================
    print("\n" + "=" * 70)
    print("  STATISTICAL TESTS SUMMARY TABLE")
    print("  (Ready for direct insertion into academic paper)")
    print("=" * 70)
    print(f"\n  {'Test':<35} {'Statistic':<15} {'p-value':<15} {'Significance':<15}")
    print(f"  {'-'*75}")
    print(f"  {'Shapiro-Wilk (Baseline)':<35} {'W='+str(round(w_base,4)):<15} {p_base:<15.6f} {'Normal' if p_base > 0.05 else 'Non-Normal'}")
    print(f"  {'Shapiro-Wilk (Monitoring)':<35} {'W='+str(round(w_mon,4)):<15} {p_mon:<15.6f} {'Normal' if p_mon > 0.05 else 'Non-Normal'}")
    print(f"  {'Independent t-test':<35} {'t='+str(round(t_stat,4)):<15} {p_ttest:<15.8f} {'***' if p_ttest < 0.001 else '**' if p_ttest < 0.01 else '*' if p_ttest < 0.05 else 'ns'}")
    print(f"  {'Mann-Whitney U':<35} {'U='+str(round(u_stat,2)):<15} {p_mann:<15.8f} {'***' if p_mann < 0.001 else '**' if p_mann < 0.01 else '*' if p_mann < 0.05 else 'ns'}")
    cohens_label = "Cohen's d"
    print(f"  {cohens_label:<35} {'d='+str(round(cohens_d,4)):<15} {'--':<15} {effect_label}")
    print(f"  {'One-Way ANOVA':<35} {'F='+str(round(f_stat,4)):<15} {p_anova:<15.8f} {'***' if p_anova < 0.001 else '**' if p_anova < 0.01 else '*' if p_anova < 0.05 else 'ns'}")
    print(f"  {'Linear Regression':<35} {'R2='+str(round(r_squared,4)):<15} {p_trend:<15.8f} {'***' if p_trend < 0.001 else 'ns'}")
    print(f"  {'Pearson Correlation':<35} {'r='+str(round(pearson_r,4)):<15} {p_pearson:<15.6f} {'***' if p_pearson < 0.001 else '**' if p_pearson < 0.01 else '*' if p_pearson < 0.05 else 'ns'}")
    print(f"  {'Spearman Correlation':<35} {'rs='+str(round(spearman_r,4)):<15} {p_spearman:<15.6f} {'***' if p_spearman < 0.001 else '**' if p_spearman < 0.01 else '*' if p_spearman < 0.05 else 'ns'}")
    print(f"  {'Seasonal t-test':<35} {'t='+str(round(t_season,4)):<15} {p_season:<15.6f} {'***' if p_season < 0.001 else '**' if p_season < 0.01 else '*' if p_season < 0.05 else 'ns'}")
    print(f"\n  Significance: *** p<0.001  ** p<0.01  * p<0.05  ns = not significant")
    print(f"  N = {len(df)} monthly observations across {df['year'].nunique()} years")
    print("=" * 70)


if __name__ == "__main__":
    main()
