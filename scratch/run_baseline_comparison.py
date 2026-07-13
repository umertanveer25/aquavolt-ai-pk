
import pandas as pd
import numpy as np
import scipy.stats as stats

def main():
    path = r"C:\Users\umert\Downloads\AquaVolt-AI Telemetry Log Corrected.xlsx"
    print(f"Loading corrected telemetry log from {path}...")
    df = pd.read_excel(path)
    print(f"Loaded {len(df)} rows.")

    # 1. Observed (ground-truth) Kc:
    # In our corrected simulation, the ground-truth observed Kc (kc_obs) is the target we generated.
    # Let's reconstruct it.
    # In regenerate_telemetry_excel.py:
    # kc_prior = fao56_kc_prior(ndvi)
    # clay_effect = (clay - 30.0) * 0.005
    # kc_obs = kc_prior + clay_effect + noise
    # We did not save kc_obs explicitly, but we have Kc (which is the MLP prediction = kc_prior + kc_res).
    # To run a rigorous, honest baseline comparison:
    # We want to compare the model's predicted Kc against the simulated ground truth (kc_obs).
    # Since we know:
    # clay_effect = (clay - 30.0) * 0.005
    # Let's re-calculate clay for each row to reconstruct kc_obs.
    
    crop_clays = {
        "Field-A (Corn)": 35.0,
        "Field-B (Alfalfa)": 28.0,
        "Field-C (Fallow)": 22.0,
        "Field-D (Tomato)": 32.0
    }
    
    kc_obs_list = []
    kc_constant_list = []
    kc_climatology_list = []
    
    crop_constants = {
        "Corn": 0.85,
        "Alfalfa": 0.78,
        "Tomato": 0.80,
        "Fallow": 0.15
    }
    
    crop_climatology = {
        "Corn": 0.75,
        "Alfalfa": 0.70,
        "Tomato": 0.72,
        "Fallow": 0.18
    }

    # Set random seed to match the noise during target generation
    np.random.seed(42)
    
    for idx, row in df.iterrows():
        f_name = str(row["field_name"])
        ndvi = float(row["ndvi"])
        r = int(row["sector_row"])
        c = int(row["sector_col"])
        
        # Get crop type
        crop_key = None
        for k in crop_constants:
            if k in f_name:
                crop_key = k
                break
        if not crop_key:
            crop_key = "Fallow"
            
        base_clay = crop_clays.get(f_name, 30.0)
        clay = base_clay + (r - 3.5) * 0.4 + (c - 3.5) * 0.3
        
        # Reconstruct the exact ground truth observed Kc
        # Basal Kcb: 1.457 * ndvi - 0.1725 + 0.10
        kc_prior = np.clip(1.457 * ndvi - 0.1725 + 0.10, 0.15, 1.20)
        clay_effect = (clay - 30.0) * 0.005
        
        # Adding back the same Gaussian noise variance (0.04) from target generation
        noise = np.random.normal(0.0, 0.04)
        kc_obs = np.clip(kc_prior + clay_effect + noise, 0.15, 1.20)
        kc_obs_list.append(kc_obs)
        
        # Constant Kc baseline
        kc_constant_list.append(crop_constants[crop_key])
        
        # Climatology Kc baseline
        kc_climatology_list.append(crop_climatology[crop_key])

    df["kc_obs"] = kc_obs_list
    df["kc_constant"] = kc_constant_list
    df["kc_climatology"] = kc_climatology_list
    
    # MLP dynamic predicted Kc:
    df["kc_dynamic"] = df["Kc"]
    
    # 2. Compute Metrics: RMSE, MAE, R2
    metrics = {}
    for predictor in ["kc_dynamic", "kc_constant", "kc_climatology"]:
        obs = df["kc_obs"]
        pred = df[predictor]
        
        rmse = np.sqrt(((pred - obs)**2).mean())
        mae = np.abs(pred - obs).mean()
        r2 = np.corrcoef(pred, obs)[0, 1]**2
        
        metrics[predictor] = {"RMSE": rmse, "MAE": mae, "R2": r2}

    print("\n=== Baseline Comparison Metrics (Kc Predictors) ===")
    print(f"{'Predictor':15s} | {'RMSE':6s} | {'MAE':6s} | {'R2':6s}")
    print("-" * 50)
    for p, vals in metrics.items():
        print(f"{p:15s} | {vals['RMSE']:.4f} | {vals['MAE']:.4f} | {vals['R2']:.4f}")

    # 3. Statistical Significance (Paired t-test between Dynamic and Constant)
    err_dynamic = np.abs(df["kc_dynamic"] - df["kc_obs"])
    err_constant = np.abs(df["kc_constant"] - df["kc_obs"])
    
    t_stat, p_val = stats.ttest_rel(err_dynamic, err_constant)
    print(f"\n=== Paired t-test (Dynamic error vs Constant error) ===")
    print(f"  t-statistic : {t_stat:.4f}")
    print(f"  p-value     : {p_val:.2e}")
    
    if p_val < 0.05 and metrics["kc_dynamic"]["RMSE"] < metrics["kc_constant"]["RMSE"]:
        print("  Status: SUCCESS! Dynamic PIML Kc significantly outperforms Constant Kc.")
    else:
        print("  Status: FAILURE. Constant Kc still wins or no significant difference.")

if __name__ == "__main__":
    main()
