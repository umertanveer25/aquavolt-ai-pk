import re

tex_path = r'C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.tex'
with open(tex_path, 'r', encoding='utf-8') as f:
    tex_text = f.read()

print("=== CHECKING FIGURE IN-TEXT CITATIONS & SUBPANELS ===")
fig_labels = ['fig:study_area', 'fig:system_arch', 'fig:validation_scatter', 'fig:validation_timeseries', 'fig:imputation_gap', 'fig:awd_redox_flux']
for fl in fig_labels:
    # Find occurrences of \ref{fl}
    matches = [m.start() for m in re.finditer(re.escape(fl), tex_text)]
    print(f"\nFigure {fl}: {len(matches)} occurrences")
    for idx, pos in enumerate(matches):
        context = tex_text[max(0, pos-150):min(len(tex_text), pos+150)].replace('\n', ' ')
        print(f"  [{idx+1}] ...{context}...")

print("\n=== CHECKING TABLE IN-TEXT CITATIONS ===")
tab_labels = ['tab:dataset_metadata', 'tab:model_hyperparams', 'tab:baseline_comparison', 'tab:methane_comparison', 'tab:ablation_study', 'tab:statistical_significance', 'tab:lit_comparison', 'tab:crop_params', 'tab:edge_benchmarks']
for tl in tab_labels:
    matches = [m.start() for m in re.finditer(re.escape(tl), tex_text)]
    print(f"\nTable {tl}: {len(matches)} occurrences")
    for idx, pos in enumerate(matches):
        context = tex_text[max(0, pos-150):min(len(tex_text), pos+150)].replace('\n', ' ')
        print(f"  [{idx+1}] ...{context}...")
