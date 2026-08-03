import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# Settings – minimalist scientific look
sns.set_style("ticks")
sns.set_palette("muted")  # premium, low‑contrast palette
sns.set_context("paper", rc={"lines.linewidth": 2.5})  # thick lines
sns.despine(trim=True)

# Simulate data
np.random.seed(42)

# distance from field edge (0‑30 m)
x = np.linspace(0, 30, 30)

# Alfalfa – exponential decay 1°C → 0°C
alfalfa_mean = np.exp(-x / 10)  # shape ~ exponential
alfalfa = alfalfa_mean * 1.0 + np.random.normal(0, 0.04, size=x.size)

# Tomato – exponential decay 0.3°C → 0°C
tomato_mean = 0.3 * np.exp(-x / 12)
Tomato = tomato_mean + np.random.normal(0, 0.02, size=x.size)

# Corn – inverted linear trend –0.15°C → 0°C
corn_mean = -0.15 + (0.15 / 30) * x
corn = corn_mean + np.random.normal(0, 0.015, size=x.size)

# Assemble long‑form DataFrame for seaborn
df = pd.DataFrame({
    "Distance (m)": np.concatenate([x, x, x]),
    "Thermal Anomaly (°C)": np.concatenate([alfalfa, Tomato, corn]),
    "Crop": ["Alfalfa"] * x.size + ["Tomato"] * x.size + ["Corn"] * x.size
})

plt.figure(figsize=(8, 5))

# seaborn automatically draws the 95 % CI envelope
sns.lineplot(
    data=df,
    x="Distance (m)",
    y="Thermal Anomaly (°C)",
    hue="Crop",
    estimator="mean",
    ci=95,
    lw=2.5
)

# Horizontal reference line at y = 0
plt.axhline(0, color="gray", linewidth=1.0, linestyle="--")

# Labels and limits
plt.xlabel("Distance from Exposed Boundary (m)", fontsize=12)
plt.ylabel(r"Canopy Thermal Anomaly ($\Delta$T, °C)", fontsize=12)
plt.xlim(0, 30)
plt.ylim(-0.18, 1.1)

plt.legend(title="Crop", loc="upper right")
plt.tight_layout()

output_path = "thermal_decay_plot.png"
plt.savefig(output_path, dpi=300, bbox_inches="tight")
plt.show()
print(f"Figure saved to: {output_path}")
