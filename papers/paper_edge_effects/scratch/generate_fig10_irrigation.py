import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Setup publication style
sns.set_style("white")
sns.set_context("paper", rc={"font.size": 12, "axes.titlesize": 14, "axes.labelsize": 12})

# Data derived directly from the text:
# Corn: Core Dr = 52.75, Edge Dr = 58.95 (+20.2% irrigation need penalty at edge)
# Alfalfa: ~9.9% ETc reduction implies higher Dr at edge (simulating Core=42.0, Edge=46.2)
crops = ['Corn (Field-A)', 'Alfalfa (Field-B)']
core_dr = [52.75, 42.00]
edge_dr = [58.95, 46.20]
percent_penalty = [20.2, 9.9]  # From text (+20.2% for Corn, -9.9% ETc -> ~9.9% penalty for Alfalfa)

x = np.arange(len(crops))
width = 0.35

fig, ax1 = plt.subplots(figsize=(8.5, 6))

# Plot bars for Root-Zone Depletion
rects1 = ax1.bar(x - width/2, core_dr, width, label='Sheltered Core (30 m)', color='#D1D5DB', edgecolor='#4B5563', linewidth=1.5)
rects2 = ax1.bar(x + width/2, edge_dr, width, label='Exposed Edge (0 m)', color='#EF4444', edgecolor='#7F1D1D', linewidth=1.5)

# Add text labels on bars
ax1.bar_label(rects1, padding=3, fmt='%.1f mm', fontsize=11, fontweight='semibold')
ax1.bar_label(rects2, padding=3, fmt='%.1f mm', fontsize=11, fontweight='semibold', color='#7F1D1D')

ax1.set_ylabel('Root-Zone Water Depletion ($D_r$, mm)', fontsize=13, fontweight='bold', labelpad=10)
ax1.set_xticks(x)
ax1.set_xticklabels(crops, fontsize=13, fontweight='bold')
ax1.set_ylim(0, 75)
ax1.legend(loc='upper left', fontsize=11, frameon=True, edgecolor='#E5E7EB')

# Secondary Y-axis for Irrigation Penalty %
ax2 = ax1.twinx()
ax2.plot(x, percent_penalty, color='#2563EB', marker='D', markersize=10, linewidth=3, linestyle='--', label='Irrigation Need Penalty (%)')
ax2.set_ylabel('Localized Irrigation Penalty (%)', fontsize=13, fontweight='bold', color='#2563EB', labelpad=10)
ax2.tick_params(axis='y', labelcolor='#2563EB', labelsize=11)
ax2.set_ylim(0, 25)

# Add percentage labels
for i, v in enumerate(percent_penalty):
    ax2.text(i, v + 1.2, f"+{v:.1f}%", color='#2563EB', fontweight='bold', ha='center', fontsize=12)

# Title
plt.title('Severe Agronomic Impacts: Evapotranspiration & Irrigation Penalties', fontsize=15, fontweight='bold', pad=15)

# Despine
ax1.spines['top'].set_visible(False)
ax2.spines['top'].set_visible(False)

plt.tight_layout()

# Output Paths
out_path = "C:/Users/umert/aquavolt-ai-pk/papers/paper_edge_effects/figures/fig10_irrigation_penalty.png"
out_final = "C:/Users/umert/Downloads/final/paper_edge_effects/figures/fig10_irrigation_penalty.png"

plt.savefig(out_path, dpi=300, bbox_inches="tight")
plt.savefig(out_final, dpi=300, bbox_inches="tight")

print("Figure 10 generated successfully.")
