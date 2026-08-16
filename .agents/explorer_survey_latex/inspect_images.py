import os
from PIL import Image

paths = [
    r'paper_latex\figures\study_area_map.png',
    r'paper_latex\figures\system_architecture.png',
    r'paper_latex\figures\validation_scatter.png',
    r'paper_latex\figures\validation_timeseries.png',
    r'paper_latex\figures\imputation_gap.png',
    r'paper_latex\fig1_prisma_final.png',
    r'paper_latex\fig2_process_final.png',
    r'paper_latex\fig3_countries_final.png',
    r'paper_latex\fig4_venues_final.png',
    r'grid_comparison.png',
    r'multi_field_annotated.png',
    r'satellite_field_annotated.png',
    r'data\real_figure_3.png',
    r'data\real_figure_4.png',
    r'data\real_figure_5.png',
]

for p in paths:
    if os.path.exists(p):
        im = Image.open(p)
        print(f"{p}: format={im.format}, size={im.size} (WxH), mode={im.mode}, filesize={os.path.getsize(p)/1024:.1f} KB")
    else:
        print(f"{p}: NOT FOUND")
