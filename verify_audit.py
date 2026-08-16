import os
import glob
import json
import math
import numpy as np
import pandas as pd
from scipy import stats

def run_empirical_audit():
    print("=" * 80)
    print("  AquaVolt-AI Empirical & Numerical Consistency Audit Suite")
    print("=" * 80)
    
    # -------------------------------------------------------------
    # 1. Memory Hub / facts.json Verification
    # -------------------------------------------------------------
    facts_path = os.path.join(".agents", "memory", "facts.json")
    if os.path.exists(facts_path):
        with open(facts_path, "r", encoding="utf-8") as f:
            facts = json.load(f)
        print("[FACTS.JSON] Successfully loaded facts.json")
        metrics = facts.get("l1_atomic_facts", {})
    else:
        print("[FACTS.JSON] WARNING: facts.json not found!")
        metrics = {}

    # -------------------------------------------------------------
    # 2. Longitudinal 8-Year Methane Analysis (2019-2026)
    # -------------------------------------------------------------
    print("\n--- [AUDIT] 8-Year Longitudinal Methane Trend Analysis ---")
    monthly_files = sorted(glob.glob(os.path.join("data", "20*", "*_methane.csv")))
    print(f"Found {len(monthly_files)} monthly methane files across data/2019-2026.")
    
    records = []
    for mf in monthly_files:
        try:
            m_df = pd.read_csv(mf)
            for _, row in m_df.iterrows():
                records.append({
                    "year": int(row["year"]),
                    "month": int(row["month"]),
                    "date_idx": int(row["year"]) * 12 + int(row["month"]),
                    "regional_methane_ppb": float(row["regional_methane_ppb"]),
                    "emission_proxy_kg_hr": float(row.get("emission_proxy_kg_hr", 0.0)),
                    "file": mf
                })
        except Exception as e:
            print(f"Error reading {mf}: {e}")
            
    df_ch4 = pd.DataFrame(records)
    print(f"Total extracted monthly records: {len(df_ch4)}")
    
    if len(df_ch4) > 0:
        baseline_mask = (df_ch4["year"] >= 2019) & (df_ch4["year"] <= 2022)
        monitoring_mask = (df_ch4["year"] >= 2023) & (df_ch4["year"] <= 2026)
        
        baseline_vals = df_ch4[baseline_mask]["regional_methane_ppb"].values
        monitoring_vals = df_ch4[monitoring_mask]["regional_methane_ppb"].values
        
        print(f"Baseline (2019-2022) Count: {len(baseline_vals)}")
        print(f"  Mean: {np.mean(baseline_vals):.2f} ppb (Claimed in paper: 1883.16)")
        print(f"  Std:  {np.std(baseline_vals, ddof=1):.2f} ppb (Claimed in paper: 17.84)")
        print(f"  Median: {np.median(baseline_vals):.2f} ppb (Claimed in paper: 1883.38)")
        
        print(f"Monitoring (2023-2026) Count: {len(monitoring_vals)}")
        print(f"  Mean: {np.mean(monitoring_vals):.2f} ppb (Claimed in paper: 1912.59)")
        print(f"  Std:  {np.std(monitoring_vals, ddof=1):.2f} ppb (Claimed in paper: 11.13)")
        print(f"  Median: {np.median(monitoring_vals):.2f} ppb (Claimed in paper: 1909.73)")
        
        # Linear Regression Trend
        # Convert month index to years elapsed
        start_idx = df_ch4["date_idx"].min()
        x_years = (df_ch4["date_idx"] - start_idx) / 12.0
        y_ppb = df_ch4["regional_methane_ppb"].values
        
        slope, intercept, r_val, p_val, std_err = stats.linregress(x_years, y_ppb)
        print(f"Linear Trend Slope: {slope:.2f} ppb/year (Claimed in paper: +8.20)")
        print(f"Linear Trend R^2:   {r_val**2:.4f} (Claimed in paper: 0.6672)")
        print(f"Linear Trend p-val: {p_val:.4e} (Claimed in paper: p < 0.001 / 8.11e-21)")
        
        # Hypothesis Testing: Baseline vs Monitoring
        t_stat, t_pval = stats.ttest_ind(baseline_vals, monitoring_vals, equal_var=False)
        print(f"Two-Sample Welch's t-test: t = {t_stat:.4f}, p = {t_pval:.4e} (Claimed: t = -9.0493, p = 1.42e-13)")
        
        u_stat, u_pval = stats.mannwhitneyu(baseline_vals, monitoring_vals, alternative='two-sided')
        print(f"Mann-Whitney U Test: U = {u_stat:.1f}, p = {u_pval:.4e} (Claimed: U = 154.0, p = 4.88e-11)")
        
        # Cohen's d
        n1, n2 = len(baseline_vals), len(monitoring_vals)
        s1, s2 = np.std(baseline_vals, ddof=1), np.std(monitoring_vals, ddof=1)
        s_pooled = np.sqrt(((n1 - 1) * s1**2 + (n2 - 1) * s2**2) / (n1 + n2 - 2))
        cohen_d = abs(np.mean(monitoring_vals) - np.mean(baseline_vals)) / s_pooled
        print(f"Cohen's d: {cohen_d:.4f} (Claimed: 1.9581)")
        
        f_stat, f_pval = stats.f_oneway(baseline_vals, monitoring_vals)
        print(f"ANOVA F-Test: F = {f_stat:.4f}, p = {f_pval:.4e} (Claimed: F = 20.5395, p = 2.15e-5)")

    # -------------------------------------------------------------
    # 3. Validation Matrix & Cross-Sensor Correlations
    # -------------------------------------------------------------
    print("\n--- [AUDIT] Sensor Validation Matrix & In-Situ Correlations ---")
    matrix_path = os.path.join("data", "sensor_validation_matrix.csv")
    if os.path.exists(matrix_path):
        df_mat = pd.read_csv(matrix_path)
        print(f"Loaded {len(df_mat)} validation records from {matrix_path}")
        
        # Ground AmeriFlux comparison
        valid_af = df_mat.dropna(subset=["our_emission_kg_hr", "ameriflux_ground_ch4_kg_hr"])
        if len(valid_af) > 0:
            our_em = valid_af["our_emission_kg_hr"].values
            af_gt = valid_af["ameriflux_ground_ch4_kg_hr"].values
            our_ppb = valid_af["our_methane_ppb"].values
            
            r_af, p_af = stats.pearsonr(our_ppb, af_gt)
            rho_af, sp_af = stats.spearmanr(our_ppb, af_gt)
            rmse_af = np.sqrt(np.mean((our_em - af_gt)**2))
            mae_af = np.mean(np.abs(our_em - af_gt))
            print(f"AmeriFlux Ground Tower (US-Tw3) [N={len(valid_af)}]:")
            print(f"  Pearson r:    {r_af:.4f} (Claimed: -0.5777)")
            print(f"  R^2:          {r_af**2:.4f} (Claimed: 0.3337)")
            print(f"  Spearman rho: {rho_af:.4f} (Claimed: -0.6053)")
            print(f"  p-value:      {p_af:.5f} (Claimed: 0.00959)")
            print(f"  RMSE:         {rmse_af:.2f} kg/hr (Claimed: 31.66 kg/hr)")
            print(f"  MAE:          {mae_af:.2f} kg/hr (Claimed: 31.5514 kg/hr in verify_mrv)")

    # -------------------------------------------------------------
    # 4. Carbon Credits & MRV Accounting
    # -------------------------------------------------------------
    print("\n--- [AUDIT] Carbon Accounting & GWP Verification ---")
    cc_path = os.path.join("data", "carbon_credit_report.csv")
    if os.path.exists(cc_path):
        df_cc = pd.read_csv(cc_path)
        base_cc = df_cc[df_cc["period"].str.contains("baseline", case=False)]
        mon_cc = df_cc[df_cc["period"].str.contains("monitoring", case=False)]
        
        sum_base_co2e = base_cc["annual_co2e_tons"].sum()
        sum_mon_co2e = mon_cc["annual_co2e_tons"].sum()
        diff_co2e = sum_mon_co2e - sum_base_co2e
        pct_diff = (diff_co2e / sum_base_co2e) * 100
        
        print(f"Carbon Credit Report (25 sub-fields):")
        print(f"  Baseline total:   {sum_base_co2e:.2f} tCO2e (verify_mrv: 14.23)")
        print(f"  Monitoring total: {sum_mon_co2e:.2f} tCO2e (verify_mrv: 26.86)")
        print(f"  Net Impact:       {diff_co2e:+.2f} tCO2e ({pct_diff:+.1f}%) (verify_mrv: +12.63 tCO2e / +88.8%)")

    # -------------------------------------------------------------
    # 5. Peak-Summer Evapotranspiration & NSE Low-Variance Proof
    # -------------------------------------------------------------
    print("\n--- [AUDIT] Evapotranspiration & NSE Mathematical Proof Verification ---")
    rmse_claimed = 0.3000
    mae_claimed = 0.2688
    mse_claimed = rmse_claimed ** 2  # 0.0900
    sigma_sq_claimed = 0.0150
    nse_theoretical = 1 - (mse_claimed / sigma_sq_claimed)
    print(f"Claimed RMSE: {rmse_claimed:.4f} mm/day -> MSE = {mse_claimed:.4f}")
    print(f"Claimed Sigma_y^2: {sigma_sq_claimed:.4f} mm^2/day^2")
    print(f"Theoretical NSE = 1 - ({mse_claimed:.4f} / {sigma_sq_claimed:.4f}) = {nse_theoretical:.4f}")
    print(f"Reported NSE in Paper: -5.0408 (Discrepancy: {abs(nse_theoretical - (-5.0408)):.4f})")
    
    # Check what exact sigma_sq would yield -5.0408:
    # 1 - (0.0900 / sigma_sq) = -5.0408 => 0.0900 / sigma_sq = 6.0408 => sigma_sq = 0.0900 / 6.0408 = 0.0148987
    sigma_sq_exact = mse_claimed / (1.0 - (-5.0408))
    print(f"Exact Sigma_y^2 required for NSE = -5.0408: {sigma_sq_exact:.6f} mm^2/day^2 (approx 0.0149)")

    # -------------------------------------------------------------
    # 6. Table 6 Statistical Significance Across 36 Epochs
    # -------------------------------------------------------------
    print("\n--- [AUDIT] Table 6 Hypothesis Testing & Statistical Significance ---")
    # Table 6 comparisons:
    comparisons = [
        {"name": "vs Bilinear", "delta_mu": -1.1280, "t_stat": -14.825, "df": 35, "cohen_d": 2.47, "ci": [-1.282, -0.974]},
        {"name": "vs Random Forest", "delta_mu": -0.5450, "t_stat": -9.641, "df": 35, "cohen_d": 1.61, "ci": [-0.660, -0.430]},
        {"name": "vs Standard LSTM", "delta_mu": -0.4240, "t_stat": -8.120, "df": 35, "cohen_d": 1.35, "ci": [-0.530, -0.318]},
        {"name": "vs Pure CNN", "delta_mu": -0.3890, "t_stat": -7.415, "df": 35, "cohen_d": 1.24, "ci": [-0.495, -0.283]},
        {"name": "vs METRIC", "delta_mu": -0.2820, "t_stat": -5.932, "df": 35, "cohen_d": 0.99, "ci": [-0.378, -0.186]},
        {"name": "vs Ablation 1 (L_p=0)", "delta_mu": -0.4420, "t_stat": -8.764, "df": 35, "cohen_d": 1.46, "ci": [-0.544, -0.340]},
    ]
    
    for comp in comparisons:
        # Check standard error and t-distribution:
        # t = delta_mu / (std / sqrt(N))
        # std_err = abs(delta_mu) / abs(t_stat)
        std_err = abs(comp["delta_mu"]) / abs(comp["t_stat"])
        s_diff = std_err * np.sqrt(36)
        # 95% critical value for df=35
        t_crit = stats.t.ppf(0.975, df=35)
        ci_lower = comp["delta_mu"] - t_crit * std_err
        ci_upper = comp["delta_mu"] + t_crit * std_err
        # p-value two-tailed
        p_val = 2 * (1 - stats.t.cdf(abs(comp["t_stat"]), df=35))
        # Cohen's d = abs(delta_mu) / s_diff
        d_calc = abs(comp["delta_mu"]) / s_diff
        
        print(f"Comparison: {comp['name']}")
        print(f"  Reported: delta_mu={comp['delta_mu']:.4f}, t={comp['t_stat']:.3f}, d={comp['cohen_d']:.2f}, CI=[{comp['ci'][0]:.3f}, {comp['ci'][1]:.3f}]")
        print(f"  Computed: t_crit={t_crit:.3f}, p_val={p_val:.4e}, d_calc={d_calc:.2f}, CI=[{ci_lower:.3f}, {ci_upper:.3f}]")
        ci_diff = max(abs(ci_lower - comp['ci'][0]), abs(ci_upper - comp['ci'][1]))
        if ci_diff > 0.01:
            print(f"  [-] NOTICE: CI discrepancy: {ci_diff:.4f}")
        else:
            print(f"  [+] CONFIRMED: Statistical values strictly verified!")

    # -------------------------------------------------------------
    # 7. Agronomic & Biophysical Constants (Table 7 vs Van Genuchten)
    # -------------------------------------------------------------
    print("\n--- [AUDIT] Biophysical Parameter Matrix (Table 7) & Hydrology Calculations ---")
    fields = [
        {"field": "Field A: Corn", "fc": 0.365, "wp": 0.185, "zr": 1.20, "p": 0.55},
        {"field": "Field B: Alfalfa", "fc": 0.365, "wp": 0.185, "zr": 1.50, "p": 0.55},
        {"field": "Field C: Fallow", "fc": 0.365, "wp": 0.185, "zr": 0.10, "p": 0.90},
        {"field": "Field D: Tomato", "fc": 0.365, "wp": 0.185, "zr": 0.90, "p": 0.40},
    ]
    for fld in fields:
        taw = 1000 * (fld["fc"] - fld["wp"]) * fld["zr"]
        raw = fld["p"] * taw
        print(f"{fld['field']}: TAW = {taw:.1f} mm, RAW = {raw:.1f} mm (delta_theta = {fld['fc'] - fld['wp']:.3f})")

    # -------------------------------------------------------------
    # 8. LoRaWAN & TinyML Energy Budget Calculations
    # -------------------------------------------------------------
    print("\n--- [AUDIT] LoRaWAN Link Budget & TinyML Solar Energy Harvester ---")
    p_tx = 14.0
    s_rx = -137.0
    g_tx = 2.15
    g_rx = 5.0
    l_cable = 1.0
    link_budget = p_tx - s_rx + g_tx + g_rx - l_cable
    print(f"LoRaWAN Link Budget: {link_budget:.2f} dB (Claimed: 157.15 dB >= 154.0 dB)")
    
    # Solar Harvesting:
    p_solar = 0.5 # W
    psh = 2.0 # Peak Sun Hours
    eta_mppt = 0.85
    eta_batt = 0.90
    e_harvest_wh = p_solar * psh * eta_mppt * eta_batt # 0.765 Wh
    e_harvest_mwh = e_harvest_wh * 1000.0 # 765.0 mWh
    e_daily_mwh = 3.372 # mWh/day
    safety_margin = e_harvest_mwh / e_daily_mwh
    print(f"Solar Harvest: {e_harvest_mwh:.1f} mWh/day (Claimed in App B: 765.0 mWh/day; in Sec 6.2: 742.0 mWh/day)")
    print(f"Solar Safety Margin: {safety_margin:.2f}x (Claimed in App B: 226.87x approx 220x)")

    print("\n" + "=" * 80)
    print("  Empirical Consistency Audit Complete!")
    print("=" * 80)

if __name__ == "__main__":
    run_empirical_audit()
