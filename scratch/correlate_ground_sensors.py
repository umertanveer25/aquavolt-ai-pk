
import pandas as pd
import numpy as np
import scipy.stats as stats
import matplotlib.pyplot as plt
import os

def main():
    log_path = r"C:\Users\umert\Downloads\AquaVolt-AI Telemetry Log Corrected.xlsx"
    scan_path = r"c:\Users\umert\aquavolt-ai-pk\data\scan_benchmark_sample.csv"
    flux_path = r"c:\Users\umert\aquavolt-ai-pk\data\ameriflux_benchmark_sample.csv"
    out_dir = r"C:\Users\umert\.gemini\antigravity\brain\8d23e27f-337c-4bdb-abe2-28bd05fbe957"
    
    print("Loading telemetry log...")
    df = pd.read_excel(log_path)
    print("Loading SCAN soil moisture benchmark...")
    df_scan = pd.read_csv(scan_path)
    print("Loading AmeriFlux tower benchmark...")
    df_flux = pd.read_csv(flux_path)

    # 1. Aggregate hourly sector-level predictions to daily field-level averages
    df["date"] = pd.to_datetime(df["timestamp"]).dt.strftime("%Y-%m-%d")
    
    # We aggregate all sectors and fields to get the daily average for comparison with ground towers
    daily_avg = df.groupby("date").agg({
        "ndvi": "mean",
        "ndwi_real": "mean",
        "savi": "mean",
        "lst": "mean",
        "Kc": "mean",
        "Ks": "mean",
        "Dr": "mean",
        "ETc": "mean",
        "soil_moisture": "mean"
    }).reset_index()

    # 2. Correlate with SCAN Soil Moisture
    # Merge on Date
    scan_merge = pd.merge(daily_avg, df_scan, left_on="date", right_on="Date", how="inner")
    print(f"\nMerged {len(scan_merge)} overlapping days with SCAN station.")
    
    if len(scan_merge) > 1:
        # Soil moisture correlation
        # Ground sensor soil moisture vs our predicted/satellite soil moisture
        # We can map our NDWI_real or soil_moisture column
        r_sm, p_sm = stats.pearsonr(scan_merge["actual_soil_moist"], scan_merge["soil_moisture"])
        rmse_sm = np.sqrt(((scan_merge["soil_moisture"] - scan_merge["actual_soil_moist"])**2).mean())
        bias_sm = (scan_merge["soil_moisture"] - scan_merge["actual_soil_moist"]).mean()
        
        print("\n=== SCAN Soil Moisture Validation ===")
        print(f"  Pearson r : {r_sm:.4f} (p = {p_sm:.2e})")
        print(f"  RMSE      : {rmse_sm:.4f} m3/m3")
        print(f"  Bias      : {bias_sm:.4f} m3/m3")
        
        # Plot SCAN Correlation
        plt.style.use('dark_background')
        fig, ax = plt.subplots(figsize=(6, 5))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        
        ax.scatter(scan_merge["actual_soil_moist"], scan_merge["soil_moisture"], color='#00d26a', alpha=0.8, edgecolors='white', s=80, label='Daily average')
        
        # Draw 1:1 line
        lims = [
            min(ax.get_xlim()[0], ax.get_ylim()[0]),
            max(ax.get_xlim()[1], ax.get_ylim()[1])
        ]
        ax.plot(lims, lims, 'w--', alpha=0.5, label='1:1 Line')
        
        ax.set_xlabel("SCAN Actual Soil Moisture (m³/m³)", color='white')
        ax.set_ylabel("AquaVolt Predicted Soil Moisture (m³/m³)", color='white')
        ax.set_title("SCAN Soil Moisture Ground Calibration", color='white', pad=15)
        ax.legend()
        ax.grid(True, alpha=0.2)
        
        plot_path = os.path.join(out_dir, "scan_correlation.png")
        plt.tight_layout()
        plt.savefig(plot_path, facecolor='#0e1117')
        plt.close()
        print(f"  Saved plot to: {plot_path}")

    # 3. Correlate with AmeriFlux Tower ET
    flux_merge = pd.merge(daily_avg, df_flux, left_on="date", right_on="Date", how="inner")
    print(f"\nMerged {len(flux_merge)} overlapping days with AmeriFlux tower.")
    
    if len(flux_merge) > 1:
        # ETc correlation
        r_et, p_et = stats.pearsonr(flux_merge["Actual_ET_mm"], flux_merge["ETc"])
        rmse_et = np.sqrt(((flux_merge["ETc"] - flux_merge["Actual_ET_mm"])**2).mean())
        bias_et = (flux_merge["ETc"] - flux_merge["Actual_ET_mm"]).mean()
        
        print("\n=== AmeriFlux Tower ET Validation ===")
        print(f"  Pearson r : {r_et:.4f} (p = {p_et:.2e})")
        print(f"  RMSE      : {rmse_et:.4f} mm/day")
        print(f"  Bias      : {bias_et:.4f} mm/day")
        
        # Plot AmeriFlux Correlation
        fig, ax = plt.subplots(figsize=(6, 5))
        fig.patch.set_facecolor('#0e1117')
        ax.set_facecolor('#0e1117')
        
        ax.scatter(flux_merge["Actual_ET_mm"], flux_merge["ETc"], color='#ff9f00', alpha=0.8, edgecolors='white', s=80, label='Daily average')
        
        # Draw 1:1 line
        lims = [
            min(ax.get_xlim()[0], ax.get_ylim()[0]),
            max(ax.get_xlim()[1], ax.get_ylim()[1])
        ]
        ax.plot(lims, lims, 'w--', alpha=0.5, label='1:1 Line')
        
        ax.set_xlabel("AmeriFlux Tower Actual ET (mm/day)", color='white')
        ax.set_ylabel("AquaVolt Predicted ETc (mm/day)", color='white')
        ax.set_title("AmeriFlux ETc Ground Calibration", color='white', pad=15)
        ax.legend()
        ax.grid(True, alpha=0.2)
        
        plot_path = os.path.join(out_dir, "ameriflux_correlation.png")
        plt.tight_layout()
        plt.savefig(plot_path, facecolor='#0e1117')
        plt.close()
        print(f"  Saved plot to: {plot_path}")

    # Copy plots to Downloads for user accessibility
    try:
        import shutil
        shutil.copy(os.path.join(out_dir, "scan_correlation.png"), r"C:\Users\umert\Downloads\scan_correlation.png")
        shutil.copy(os.path.join(out_dir, "ameriflux_correlation.png"), r"C:\Users\umert\Downloads\ameriflux_correlation.png")
        print("\nCopied both plots to C:\\Users\\umert\\Downloads\\ for easy viewing!")
    except Exception as e:
        print(f"Error copying plots: {e}")

if __name__ == "__main__":
    main()
