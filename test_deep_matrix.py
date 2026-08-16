import os
import pandas as pd
import numpy as np
from scipy import stats

def deep_matrix_test():
    # Test AmeriFlux correlation with emission_kg_hr
    df = pd.read_csv("data/sensor_validation_matrix.csv")
    valid = df.dropna(subset=["our_emission_kg_hr", "ameriflux_ground_ch4_kg_hr"])
    
    em = valid["our_emission_kg_hr"].values
    af = valid["ameriflux_ground_ch4_kg_hr"].values
    ppb = valid["our_methane_ppb"].values
    
    print("AmeriFlux Correlation against our_emission_kg_hr:")
    r_em, p_em = stats.pearsonr(em, af)
    rho_em, sp_em = stats.spearmanr(em, af)
    print(f"  Pearson r:    {r_em:.4f}, R2: {r_em**2:.4f}, p: {p_em:.5f}")
    print(f"  Spearman rho: {rho_em:.4f}, p: {sp_em:.5f}")
    
    print("\nAmeriFlux Correlation against our_methane_ppb:")
    r_ppb, p_ppb = stats.pearsonr(ppb, af)
    rho_ppb, sp_ppb = stats.spearmanr(ppb, af)
    print(f"  Pearson r:    {r_ppb:.4f}, R2: {r_ppb**2:.4f}, p: {p_ppb:.5f}")
    print(f"  Spearman rho: {rho_ppb:.4f}, p: {sp_ppb:.5f}")

    # Check ANOVA across 4 periods (biennial)
    import glob
    monthly_files = sorted(glob.glob(os.path.join("data", "20*", "*_methane.csv")))
    records = []
    for mf in monthly_files:
        m_df = pd.read_csv(mf)
        for _, row in m_df.iterrows():
            y = int(row["year"])
            period = "2019-2020" if y <= 2020 else ("2021-2022" if y <= 2022 else ("2023-2024" if y <= 2024 else "2025-2026"))
            records.append({"ppb": float(row["regional_methane_ppb"]), "period": period, "year": y})
    df_all = pd.DataFrame(records)
    
    groups = [group["ppb"].values for _, group in df_all.groupby("period")]
    f_4p, p_4p = stats.f_oneway(*groups)
    print(f"\nANOVA across 4 Biennial Periods (2019-2020, 2021-2022, 2023-2024, 2025-2026):")
    print(f"  F-stat: {f_4p:.4f}, p-value: {p_4p:.4e} (Paper claims F = 20.5395, p = 2.15e-5)")

    # Check annual ANOVA (8 years)
    groups_yr = [group["ppb"].values for _, group in df_all.groupby("year")]
    f_yr, p_yr = stats.f_oneway(*groups_yr)
    print(f"\nANOVA across 8 Individual Years:")
    print(f"  F-stat: {f_yr:.4f}, p-value: {p_yr:.4e}")

if __name__ == "__main__":
    deep_matrix_test()
