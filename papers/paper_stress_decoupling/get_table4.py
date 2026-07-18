import pandas as pd
import numpy as np

print("Loading data...")
df = pd.read_excel(r'C:\Users\umert\aquavolt-ai-pk\papers\paper_stress_decoupling\data\AquaVolt-AI Telemetry Log (1).xlsx', engine='openpyxl')
df = df[df['scene_id'] != 'Fallback']
df = df[~df['field_name'].str.contains('Fallow', na=True)]
df = df.groupby(['timestamp','field_name','sector_row','sector_col'], as_index=False).mean(numeric_only=True)
df['field_name'] = df['field_name'].astype(str)

# Calculate VPD and delta_T
df['es'] = 0.6108 * np.exp(17.27 * df['air_temp'] / (df['air_temp'] + 237.3))
df['ea'] = df['es'] * df['humidity'] / 100
df['VPD'] = df['es'] - df['ea']
df['delta_T'] = df['lst'] - df['air_temp']

# Classify stress
def classify(r):
    ks = r['Ks'] < 1.0
    th = r['delta_T'] >= 2.0
    vp = r['VPD'] >= 1.5
    if not ks and not th: return 'NS'
    elif ks and th: return 'Coupled'
    elif not ks and th and vp: return 'Decoupled'
    elif ks and not th: return 'Masked'
    return 'NS'

df['sc'] = df.apply(classify, axis=1)

# Extract date
df['datetime'] = pd.to_datetime(df['timestamp'])
df['date_str'] = df['datetime'].dt.strftime('%d %b %Y')

# Group by date
daily = df.groupby('date_str').agg(
    mean_vpd=('VPD', 'mean'),
    mean_dt=('delta_T', 'mean'),
    decoupled_count=('sc', lambda x: (x == 'Decoupled').sum()),
    stress_count=('sc', lambda x: (x != 'NS').sum())
).reset_index()

daily['dsi'] = daily.apply(lambda r: r['decoupled_count']/r['stress_count'] if r['stress_count'] > 0 else 0.0, axis=1)

# Sort chronologically
daily['date_dt'] = pd.to_datetime(daily['date_str'], format='%d %b %Y')
daily = daily.sort_values('date_dt').reset_index(drop=True)

# Generate LaTeX lines
print("\n=== LATEX TABLE 4 ROWS ===")
for idx, r in daily.iterrows():
    date_formatted = r['date_str'].replace(" 2026", "")
    print(f"{date_formatted} & {r['mean_vpd']:.2f} & {r['mean_dt']:.2f} & {r['dsi']:.4f} \\\\")
