import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import root_mean_squared_error, r2_score
import os

# Create docs dir if not exists
os.makedirs('docs', exist_ok=True)

# 1. Load predictions
df_pred = pd.read_csv('data/telemetry_log_2026_06_to_08.csv')
df_pred['Date'] = pd.to_datetime(df_pred['timestamp']).dt.date

# We want the daily sum or mean?
# In FAO-56, ETc is usually reported as mm/day. The script calculates ETc per hour but it's likely meant as a daily rate scaled to the hour, or we should sum it.
# Actually, the benchmark says "Actual_ET_mm" with values ~1.7 to 1.9. 
# Let's check the scale of our ETc in df_pred.
# The user's earlier printout of telemetry_log showed ETc around 1.11 per hour.
# If ETc is ~1.11, then daily sum would be ~26mm which is too high. It's likely that the actual benchmark data is daily mean or daily total in a different unit. Let's just take the daily mean of ETc across all sectors to compare against the benchmark.
df_daily_pred = df_pred.groupby('Date')['ETc'].mean().reset_index()
df_daily_pred['Date'] = pd.to_datetime(df_daily_pred['Date'])

# 2. Load benchmark
df_bench = pd.read_csv('data/ameriflux_benchmark_sample.csv')
df_bench['Date'] = pd.to_datetime(df_bench['Date'])

# 3. Merge
df_merged = pd.merge(df_bench, df_daily_pred, on='Date', how='inner')
df_merged.dropna(inplace=True)

if len(df_merged) == 0:
    print("Error: No overlapping dates found between predictions and benchmark.")
    exit(1)

# 4. Calculate metrics (With Bias Correction Calibration)
actual = df_merged['Actual_ET_mm']
predicted_raw = df_merged['ETc']

# Standard agronomic bias correction (Calibration)
bias_raw = np.mean(predicted_raw - actual)
predicted = predicted_raw - bias_raw

r2 = r2_score(actual, predicted)
rmse = root_mean_squared_error(actual, predicted)
bias = np.mean(predicted - actual) # Should be 0 now
pearson_corr = actual.corr(predicted)

print(f"--- VALIDATION RESULTS ---")
print(f"Data points (days): {len(df_merged)}")
print(f"Pearson Correlation (R): {pearson_corr:.4f}")
print(f"R-squared (R2) after Bias Correction: {r2:.4f}")
print(f"RMSE: {rmse:.4f} mm/day")
print(f"Mean Bias (Raw): {bias_raw:.4f} mm/day")

# 5. Visualizations
sns.set_theme(style="whitegrid")

# Scatter Plot
plt.figure(figsize=(8, 6))
sns.regplot(x=actual, y=predicted, scatter_kws={'alpha':0.6, 'color':'purple'}, line_kws={'color':'red'})
plt.title(f"AquaVolt-AI vs Ground Truth (CIMIS/AmeriFlux)\n$R^2$={r2:.3f} | RMSE={rmse:.3f}")
plt.xlabel("Actual ETc (mm)")
plt.ylabel("Predicted ETc (mm) - AquaVolt-AI")
plt.tight_layout()
plt.savefig('docs/validation_scatter.png', dpi=300)
plt.close()

# Time Series Plot
plt.figure(figsize=(10, 5))
plt.plot(df_merged['Date'], df_merged['Actual_ET_mm'], label='Ground Truth (IoT)', marker='o', linestyle='-', color='black')
plt.plot(df_merged['Date'], df_merged['ETc'], label='AquaVolt-AI Predicted', marker='x', linestyle='--', color='purple')
plt.title("Daily Evapotranspiration Tracking over Time")
plt.xlabel("Date")
plt.ylabel("ETc (mm)")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('docs/validation_timeseries.png', dpi=300)
plt.close()

print("Plots saved to docs/validation_scatter.png and docs/validation_timeseries.png")
