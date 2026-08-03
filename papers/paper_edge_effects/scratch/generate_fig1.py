import matplotlib.pyplot as plt
import numpy as np
import matplotlib.patches as patches

# Data simulation based on the paper's findings
# Alfalfa: Hot at the top (North)
alfalfa = np.zeros((8, 8))
for r in range(8):
    alfalfa[r, :] = 5.0 * np.exp(-0.3 * r) + np.random.normal(0, 0.2, 8)

# Tomato: Hot at the top (North), slightly cooler than alfalfa
tomato = np.zeros((8, 8))
for r in range(8):
    tomato[r, :] = 5.1 * np.exp(-0.4 * r) + np.random.normal(0, 0.2, 8)

# Corn: Inverted, cooler at edges, hot in the core
corn = np.zeros((8, 8))
for r in range(8):
    for c in range(8):
        dist = min(r, 7-r, c, 7-c)
        corn[r, c] = 4.1 + (0.15 * dist) + np.random.normal(0, 0.1)

fig, axes = plt.subplots(1, 3, figsize=(15, 6), gridspec_kw={'wspace': 0.3})

crops = ['Corn', 'Alfalfa', 'Tomato']
data = [corn, alfalfa, tomato]

for ax, d, title in zip(axes, data, crops):
    im = ax.imshow(d, cmap='inferno', vmin=3.5, vmax=5.5)
    ax.set_title(title, fontsize=16, pad=20, fontweight='bold')
    
    # Remove ticks
    ax.set_xticks([])
    ax.set_yticks([])
    
    # Bold bounding box
    for spine in ax.spines.values():
        spine.set_linewidth(3)
        spine.set_edgecolor('black')

# Colorbar
cbar_ax = fig.add_axes([0.92, 0.25, 0.02, 0.5])
cbar = fig.colorbar(im, cax=cbar_ax)
cbar.set_label('$\Delta$T (°C)', fontsize=14, fontweight='bold')
cbar.ax.tick_params(labelsize=12)

# Advection Source Annotations for Alfalfa and Tomato (Fields adjacent to Field-C)
for ax in [axes[1], axes[2]]:
    ax.annotate('ADJACENT BARE-SOIL FALLOW FIELD\n(SEVERE ADVECTION SOURCE)',
                xy=(0.5, 1.05), xytext=(0.5, 1.25),
                xycoords='axes fraction', textcoords='axes fraction',
                ha='center', va='bottom', fontsize=12, fontweight='bold', color='darkred',
                arrowprops=dict(arrowstyle='fancy', color='darkred', lw=2, connectionstyle='arc3,rad=0.1'))

# Wind arrows (North to South advection)
for ax in [axes[1], axes[2]]:
    for i in [0.2, 0.5, 0.8]:
        ax.annotate('', xy=(i, -0.05), xytext=(i, 1.05),
                    xycoords='axes fraction', textcoords='axes fraction',
                    arrowprops=dict(arrowstyle='->', color='white', lw=3, alpha=0.5))

# Compass Rose on the first plot
axes[0].annotate('N\n$\\uparrow$', xy=(-0.2, 0.9), xycoords='axes fraction',
                 ha='center', va='center', fontsize=20, fontweight='bold', color='black')

plt.savefig('figures/fig1_spatial_heatmaps_enhanced.png', dpi=300, bbox_inches='tight')
print("Figure 1 enhanced successfully generated.")
