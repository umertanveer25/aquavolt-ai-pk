import os
import re
import sys
import subprocess
import json

TEX_PATH = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.tex"
BIB_PATH = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-bibliography.bib"
PDF_PATH = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.pdf"
FIG_DIR = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\figures"

results = {}

# 1. Parse BibTeX
with open(BIB_PATH, 'r', encoding='utf-8') as f:
    bib_content = f.read()

bib_keys = set(re.findall(r'@\w+\s*\{\s*([^,\s]+)\s*,', bib_content))
print(f"Total BibTeX keys found: {len(bib_keys)}")
results["bib_keys_count"] = len(bib_keys)

# 2. Parse TeX citations
with open(TEX_PATH, 'r', encoding='utf-8') as f:
    tex_content = f.read()

# Extract all \cite{...}, \citep{...}, \citet{...}, \citeauthor{...}, etc.
cite_matches = re.findall(r'\\cite[a-zA-Z]*\{([^}]+)\}', tex_content)
tex_keys = set()
for match in cite_matches:
    for key in match.split(','):
        clean_key = key.strip()
        if clean_key:
            tex_keys.add(clean_key)

print(f"Total unique citation keys in TeX: {len(tex_keys)}")
results["tex_keys_count"] = len(tex_keys)

missing_in_bib = tex_keys - bib_keys
unused_in_tex = bib_keys - tex_keys

print(f"Keys in TeX but missing in Bib: {missing_in_bib}")
print(f"Keys in Bib but unused in TeX: {unused_in_tex}")
results["missing_in_bib"] = list(missing_in_bib)
results["unused_in_tex"] = list(unused_in_tex)
results["bijective_match"] = (len(missing_in_bib) == 0 and len(unused_in_tex) == 0)

# 3. Placeholder / Quality / Cheating Check
placeholders = re.findall(r'(?i)\b(TODO|FIXME|TBD|XXX|LOREM IPSUM|PLACEHOLDER|INSERT HERE)\b', tex_content)
print(f"Placeholders found in TeX: {placeholders}")
results["placeholders"] = placeholders

# 4. Figures & Tables in TeX
figures_in_tex = re.findall(r'\\begin\{figure\}', tex_content)
subfigures_in_tex = re.findall(r'\\begin\{subfigure\}', tex_content)
tables_in_tex = re.findall(r'\\begin\{table\*?\}', tex_content)
equations_in_tex = re.findall(r'\\begin\{equation\*?\}', tex_content)

print(f"Figures in TeX: {len(figures_in_tex)}")
print(f"Tables in TeX: {len(tables_in_tex)}")
print(f"Equations in TeX: {len(equations_in_tex)}")
results["figures_count"] = len(figures_in_tex)
results["tables_count"] = len(tables_in_tex)
results["equations_count"] = len(equations_in_tex)

# Check specific figures (fig1 to fig6)
for i in range(1, 7):
    fig_pattern = rf'fig{i}\.(jpg|png|pdf|eps)'
    found_in_tex = bool(re.search(fig_pattern, tex_content, re.IGNORECASE))
    print(f"Figure {i} referenced in TeX: {found_in_tex}")
    results[f"fig{i}_in_tex"] = found_in_tex

# Check specific tables (Table 1 to Table 7)
for i in range(1, 8):
    tab_pattern = rf'label\{{tab:.*table{i}|tab:.*tab{i}|tab:{i}\}}'
    found_label = bool(re.search(rf'label\{{tab:[^}}]*\b({i}|table{i}|tab{i})\b', tex_content, re.IGNORECASE) or 
                      f"Table {i}" in tex_content or f"tab:{i}" in tex_content or f"tab:table{i}" in tex_content)
    print(f"Table {i} presence check: {found_label}")

# Specific check for Table 6 (Literature) and Table 7 (Soil & Crop Biophysical Parameter Matrix)
results["table6_literature_check"] = bool(re.search(r'Schuit.*Falk.*Varon.*Wang', tex_content, re.DOTALL))
results["table7_biophysical_check"] = bool(re.search(r'Corn.*Alfalfa.*Fallow.*Tomato', tex_content, re.DOTALL) and re.search(r'Dual Crop Coefficient', tex_content, re.IGNORECASE))
print(f"Table 6 (Literature Matrix) content check: {results['table6_literature_check']}")
print(f"Table 7 (Biophysical Parameter Matrix) content check: {results['table7_biophysical_check']}")

# Figure 6 AWD/redox/methane check
results["fig6_redox_methane_check"] = bool(re.search(r'fig6.*redox.*methane', tex_content, re.IGNORECASE | re.DOTALL) or re.search(r'redox.*mV.*methane.*fig6', tex_content, re.IGNORECASE | re.DOTALL))
print(f"Figure 6 AWD/redox/methane text check: {results['fig6_redox_methane_check']}")

# Word count estimation (excluding LaTeX commands)
clean_text = re.sub(r'\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?', ' ', tex_content)
clean_text = re.sub(r'[%].*', ' ', clean_text)
words = re.findall(r'\b[a-zA-Z0-9_\-]+\b', clean_text)
print(f"Estimated Word Count in sn-article.tex: {len(words)}")
results["estimated_word_count"] = len(words)

with open(r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\.agents\auditor_victory_1\audit_preliminary.json", "w") as f:
    json.dump(results, f, indent=2)
print("Preliminary audit written to audit_preliminary.json")
