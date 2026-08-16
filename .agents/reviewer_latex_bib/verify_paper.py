import os
import re
import sys

tex_path = r'C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.tex'
bib_path = r'C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-bibliography.bib'

with open(bib_path, 'r', encoding='utf-8') as f:
    bib_text = f.read()

with open(tex_path, 'r', encoding='utf-8') as f:
    tex_text = f.read()

print("=================================================================")
print("=== 1. BIBTEX PARSING AND INTEGRITY CHECK ===")
print("=================================================================")

# Match BibTeX entries
entry_blocks = re.findall(r'@(\w+)\s*\{\s*([^,]+),\s*(.*?)\n\}', bib_text, re.DOTALL)
print(f"Total BibTeX entries parsed: {len(entry_blocks)}")

bib_dict = {}
entry_types = {}
missing_required = {}
year_list = []

for entry_type, key, body in entry_blocks:
    key = key.strip()
    entry_types[entry_type] = entry_types.get(entry_type, 0) + 1
    
    # Extract fields
    field_matches = re.findall(r'(\w+)\s*=\s*[\{"](.*?)[}"]\s*(?:,|$)', body, re.DOTALL)
    fields = {k.lower(): v.strip() for k, v in field_matches}
    bib_dict[key] = {'type': entry_type, 'fields': fields, 'raw': body}
    
    req = ['author', 'title', 'year']
    for r in req:
        if r not in fields:
            missing_required.setdefault(key, []).append(r)
            
    if 'year' in fields:
        y_match = re.search(r'\b(19\d\d|20\d\d)\b', fields['year'])
        if y_match:
            year_list.append(int(y_match.group(1)))

print(f"Entry Types: {entry_types}")
print(f"Missing required fields (author/title/year): {len(missing_required)}")
if missing_required:
    for k, v in missing_required.items():
        print(f"  - {k}: missing {v}")

if year_list:
    print(f"Publication Year Range: {min(year_list)} - {max(year_list)}")
    recent_2020 = sum(1 for y in year_list if y >= 2020)
    print(f"Recent papers (>= 2020): {recent_2020}/{len(year_list)} ({recent_2020/len(year_list)*100:.1f}%)")
    recent_2022 = sum(1 for y in year_list if y >= 2022)
    print(f"Recent papers (>= 2022): {recent_2022}/{len(year_list)} ({recent_2022/len(year_list)*100:.1f}%)")

print("\n=================================================================")
print("=== 2. CITATION CROSS-REFERENCE VERIFICATION ===")
print("=================================================================")

# Extract all \cite, \citep, \citet commands
cites_raw = re.findall(r'\\cite(?:p|t|alt|alp|author|year)?\*?\{([^}]+)\}', tex_text)
cited_keys = []
for c in cites_raw:
    keys = [k.strip() for k in c.split(',') if k.strip()]
    cited_keys.extend(keys)

unique_cited_keys = sorted(list(set(cited_keys)))
print(f"Total in-text citation instances: {len(cited_keys)}")
print(f"Total unique keys cited in sn-article.tex: {len(unique_cited_keys)}")

bib_keys = sorted(list(bib_dict.keys()))
missing_in_bib = [k for k in unique_cited_keys if k not in bib_dict]
orphan_in_bib = [k for k in bib_keys if k not in unique_cited_keys]

print(f"Missing keys in BibTeX: {len(missing_in_bib)}")
if missing_in_bib:
    print("  Missing:", missing_in_bib)

print(f"Orphan keys in BibTeX (uncited): {len(orphan_in_bib)}")
if orphan_in_bib:
    print("  Orphan:", orphan_in_bib)

# Check citation distribution across sections
sections = re.split(r'\\section\*?\{([^}]+)\}', tex_text)
print("\nCitation count by section:")
for i in range(1, len(sections), 2):
    sec_title = sections[i]
    sec_body = sections[i+1]
    sec_cites = re.findall(r'\\cite(?:p|t|alt|alp|author|year)?\*?\{([^}]+)\}', sec_body)
    sec_keys = []
    for c in sec_cites:
        sec_keys.extend([k.strip() for k in c.split(',') if k.strip()])
    print(f"  - Section '{sec_title}': {len(sec_keys)} citations ({len(set(sec_keys))} unique)")

print("\n=================================================================")
print("=== 3. TABLE ENVIRONMENTS VERIFICATION ===")
print("=================================================================")

table_blocks = re.findall(r'(\\begin\{(table\*?)\}(.*?)\\end\{\2\})', tex_text, re.DOTALL)
print(f"Total table environments in sn-article.tex: {len(table_blocks)}")

table_labels = []
for idx, (full_block, env, content) in enumerate(table_blocks, 1):
    cap_match = re.search(r'\\caption\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', content)
    lbl_match = re.search(r'\\label\{([^}]+)\}', content)
    tab_match = re.findall(r'\\begin\{(tabular\*?|tabularx|array)\}(?:\{([^}]+)\})?', content)
    
    cap = cap_match.group(1).replace('\n', ' ') if cap_match else "NONE"
    lbl = lbl_match.group(1) if lbl_match else "NONE"
    if lbl != "NONE":
        table_labels.append(lbl)
        
    ref_count = len(re.findall(r'\\ref\{' + re.escape(lbl) + r'\}', tex_text)) if lbl != "NONE" else 0
    
    print(f"\nTable #{idx} ({env}):")
    print(f"  Label: {lbl} (Referenced in text: {ref_count} times)")
    print(f"  Tabular spec: {tab_match}")
    print(f"  Caption: {cap[:120]}...")
    # Check booktabs usage
    has_toprule = '\\toprule' in content
    has_midrule = '\\midrule' in content
    has_bottomrule = '\\bottomrule' in content
    print(f"  Booktabs formatting: toprule={has_toprule}, midrule={has_midrule}, bottomrule={has_bottomrule}")

print("\n=================================================================")
print("=== 4. FIGURE ENVIRONMENTS & SUBPANELS VERIFICATION ===")
print("=================================================================")

fig_blocks = re.findall(r'(\\begin\{(figure\*?)\}(.*?)\\end\{\2\})', tex_text, re.DOTALL)
print(f"Total figure environments in sn-article.tex: {len(fig_blocks)}")

for idx, (full_block, env, content) in enumerate(fig_blocks, 1):
    cap_match = re.search(r'\\caption\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', content)
    lbl_match = re.search(r'\\label\{([^}]+)\}', content)
    inc_graphics = re.findall(r'\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}', content)
    
    cap = cap_match.group(1).replace('\n', ' ') if cap_match else "NONE"
    lbl = lbl_match.group(1) if lbl_match else "NONE"
    
    ref_count = len(re.findall(r'\\ref\{' + re.escape(lbl) + r'\}', tex_text)) if lbl != "NONE" else 0
    subpanels = re.findall(r'[\(\[]([a-d])[\)\]]', cap)
    
    print(f"\nFigure #{idx} ({env}):")
    print(f"  Label: {lbl} (Referenced in text: {ref_count} times)")
    print(f"  Graphics: {inc_graphics}")
    for g in inc_graphics:
        # Check if file exists relative to paper_latex or root
        p1 = os.path.join(r'C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex', g)
        p2 = os.path.join(r'C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk', g)
        exists = os.path.exists(p1) or os.path.exists(p2) or os.path.exists(p1 + '.png') or os.path.exists(p1 + '.jpg') or os.path.exists(p1 + '.pdf')
        print(f"    File '{g}' exists: {exists}")
    print(f"  Subpanels in caption: {subpanels}")
    print(f"  Caption: {cap[:140]}...")

print("\n=================================================================")
print("=== 5. MATHEMATICAL & STRUCTURAL QUALITY ===")
print("=================================================================")

eq_blocks = re.findall(r'\\begin\{(equation\*?|align\*?|gather\*?)\}(.*?)\\end\{\1\}', tex_text, re.DOTALL)
print(f"Numbered / Displayed Math Environments: {len(eq_blocks)}")
for idx, (env, content) in enumerate(eq_blocks, 1):
    lbl = re.search(r'\\label\{([^}]+)\}', content)
    lbl_str = lbl.group(1) if lbl else "no-label"
    print(f"  Eq #{idx} ({env}): label={lbl_str}")

# Check Section structure
sec_matches = re.findall(r'\\(section|subsection|subsubsection|paragraph)\*?\{([^}]+)\}', tex_text)
print(f"\nTotal Headings: {len(sec_matches)}")
for lvl, title in sec_matches:
    indent = "  " if lvl == "section" else "    " if lvl == "subsection" else "      "
    print(f"{indent}[{lvl}] {title}")

# Check for undefined or unresolved markers
print("\n=================================================================")
print("=== 6. ARTIFACT & PLACEHOLDER AUDIT ===")
print("=================================================================")
placeholders = re.findall(r'(\bTODO\b|\bTBD\b|\bFIXME\b|\bXXX\b|\?\?|\[\?\]|\\textbf\{INSERT|\bLorem\b|\bipsum\b)', tex_text, re.IGNORECASE)
print(f"Potential placeholder tokens found: {placeholders}")

# Check for unescaped percent or dollar signs or ampersands
raw_lines = tex_text.split('\n')
for line_idx, line in enumerate(raw_lines, 1):
    if re.search(r'(?<!\\)%(?!\s*$)', line):
        pass # standard comment
    # check for suspicious unescaped characters outside equations/tables
