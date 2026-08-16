import os
import numpy as np
import matplotlib.pyplot as plt

ART_DIR = r"C:\Users\umert\.gemini\antigravity\brain\3924f3fd-e810-4763-a571-e7315616bc0e"
fig_path = os.path.join(ART_DIR, "fig6.jpg")

# Set clean publication style
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'font.family': 'serif',
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 11,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.titlesize': 12
})

# Time axis (30 days, hourly resolution)
time = np.linspace(0, 30, 720)

# Simulate Water Depth (cm) under alternate wetting and drying (AWD)
# We have 3 cycles of flooding and drying
water_depth = 5.0 * np.sin(2 * np.pi * time / 10) + 1.0 * np.sin(2 * np.pi * time / 5) - 2.0
# Bound water depth: flood up to +5cm, dry down to -15cm
water_depth = np.clip(water_depth, -15.0, 5.0)

# Simulate Soil Redox Potential Eh (mV)
# Saturated soil -> anaerobic -> Eh drops to -250 mV
# Dry soil -> aerobic -> Eh rises to +200 mV
# There is a time lag of about 1.5 days for Eh changes
eh = np.zeros_like(time)
current_eh = 150.0  # start aerobic
for i in range(len(time)):
    if water_depth[i] > 0:
        # anaerobic decay: target is -200 mV
        current_eh += (-200.0 - current_eh) * 0.05
    else:
        # aerobic oxidation: target is +150 mV
        current_eh += (150.0 - current_eh) * 0.08
    eh[i] = current_eh

# Methane Flux (mg CH4 / m^2 / h)
# Methane production occurs only when Eh < -150 mV
methane_flux = np.zeros_like(time)
for i in range(len(time)):
    if eh[i] < -150.0:
        # Flux increases as Eh gets more negative
        methane_flux[i] = 12.0 * ((eh[i] + 150.0) / -100.0)**2 + np.random.normal(0, 0.5)
    else:
        methane_flux[i] = np.clip(0.1 + np.random.normal(0, 0.05), 0, 1)

# Plotting
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(7, 6), sharex=True, dpi=300)

# Plot 1: Water Depth
ax1.plot(time, water_depth, color='#1f77b4', linewidth=1.8, label='Perched Water Table Depth')
ax1.axhline(0, color='gray', linestyle='--', linewidth=0.8)
ax1.fill_between(time, water_depth, 0, where=(water_depth > 0), color='#1f77b4', alpha=0.3, label='Flooding Phase')
ax1.fill_between(time, water_depth, 0, where=(water_depth <= 0), color='#8c564b', alpha=0.15, label='Drying/Aerobic Phase')
ax1.set_ylabel('Water Level (cm)', color='#1f77b4')
ax1.tick_params(axis='y', labelcolor='#1f77b4')
ax1.set_ylim(-18, 8)
ax1.set_title('Alternate Wetting and Drying (AWD) Water Level Fluctuations')
ax1.legend(loc='upper right', frameon=True)

# Plot 2: Redox Potential and Methane Flux
color = '#d62728'
ax2.plot(time, eh, color=color, linewidth=1.5, linestyle='-', label='Soil Redox Potential ($E_h$)')
ax2.axhline(-150, color='red', linestyle=':', linewidth=1.0, label='Methanogenesis Threshold ($-150$ mV)')
ax2.set_ylabel('Redox Potential $E_h$ (mV)', color=color)
ax2.tick_params(axis='y', labelcolor=color)
ax2.set_ylim(-280, 220)

# Twin axis for Methane Flux
ax2_twin = ax2.twinx()
color_twin = '#2ca02c'
ax2_twin.plot(time, methane_flux, color=color_twin, linewidth=1.8, linestyle='-.', label='Methane Flux ($CH_4$)')
ax2_twin.set_ylabel('Methane Flux ($mg\\ CH_4\\ m^{-2}\\ h^{-1}$)', color=color_twin)
ax2_twin.tick_params(axis='y', labelcolor=color_twin)
ax2_twin.set_ylim(-1, 15)

# Combine legends
lines1, labels1 = ax2.get_legend_handles_labels()
lines2, labels2 = ax2_twin.get_legend_handles_labels()
ax2.legend(lines1 + lines2, labels1 + labels2, loc='upper right', frameon=True)
ax2.set_title('Soil Redox Potential ($E_h$) Response and Methane Flux Dynamics')
ax2.set_xlabel('Time (Days)')

plt.tight_layout()
plt.savefig(fig_path, bbox_inches='tight')
plt.close()

print(f"[SUCCESS] Programmatic Figure 6 generated and saved to: {fig_path}")
