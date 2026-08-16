import os
import re

tex_path = r'C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.tex'
with open(tex_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in sn-article.tex: {len(lines)}")

# 1. Check for raw unescaped double quotes (e.g. "word" instead of ``word'')
raw_quotes = []
for idx, l in enumerate(lines, 1):
    # Ignore comments
    l_no_comm = re.sub(r'(?<!\\)%.*$', '', l)
    # Match double quotes outside LaTeX commands
    if '"' in l_no_comm:
        raw_quotes.append((idx, l.strip()))

print(f"\n1. Lines with ASCII double quotes (\"): {len(raw_quotes)}")
for idx, l in raw_quotes[:10]:
    print(f"   Line {idx}: {l[:90]}")

# 2. Check for bare numbers before units (e.g. '10 m' instead of '$10\\text{ m}$' or '10~m')
bare_units = []
for idx, l in enumerate(lines, 1):
    l_no_comm = re.sub(r'(?<!\\)%.*$', '', l)
    m = re.findall(r'(?<![\$\w\\])\b(\d+(?:\.\d+)?)\s+(mm|cm|m|km|ha|ha-1|kg|hr|s|ms|mW|dB|mV|ppm|ppb)\b(?![\w\$])', l_no_comm)
    if m:
        bare_units.append((idx, m, l.strip()[:80]))

print(f"\n2. Bare units outside math mode instances: {len(bare_units)}")
for idx, units, l in bare_units[:10]:
    print(f"   Line {idx}: {units} -> {l}")

# 3. Check for unescaped percent signs
raw_pct = []
for idx, l in enumerate(lines, 1):
    # Check if there is an unescaped % preceded by a digit or text (not starting a comment)
    m = re.search(r'(\d+)\s*%(?!\w)', l)
    if m:
        raw_pct.append((idx, m.group(0), l.strip()[:80]))

print(f"\n3. Unescaped percent signs after numbers: {len(raw_pct)}")
for idx, m, l in raw_pct:
    print(f"   Line {idx}: '{m}' in {l}")

# 4. Check for unresolved question marks in text (like ?? or [?])
qmarks = []
for idx, l in enumerate(lines, 1):
    l_no_comm = re.sub(r'(?<!\\)%.*$', '', l)
    if '??' in l_no_comm or '[?]' in l_no_comm or '(\\?)' in l_no_comm:
        qmarks.append((idx, l.strip()))

print(f"\n4. Unresolved question marks: {len(qmarks)}")
for idx, l in qmarks:
    print(f"   Line {idx}: {l}")

# 5. Check equation balance
math_env_open = 0
for idx, l in enumerate(lines, 1):
    if '\\begin{equation' in l or '\\begin{align' in l or '\\begin{gather' in l:
        math_env_open += 1
    if '\\end{equation' in l or '\\end{align' in l or '\\end{gather' in l:
        math_env_open -= 1

print(f"\n5. Math environment balance: {'BALANCED (0)' if math_env_open == 0 else f'UNBALANCED ({math_env_open})'}")

# 6. Check table environment balance
table_env_open = 0
for idx, l in enumerate(lines, 1):
    if '\\begin{table' in l:
        table_env_open += 1
    if '\\end{table' in l:
        table_env_open -= 1
    if '\\begin{tabular' in l:
        table_env_open += 1
    if '\\end{tabular' in l:
        table_env_open -= 1

print(f"\n6. Table / tabular environment balance: {'BALANCED (0)' if table_env_open == 0 else f'UNBALANCED ({table_env_open})'}")

# 7. Check figure environment balance
fig_env_open = 0
for idx, l in enumerate(lines, 1):
    if '\\begin{figure' in l:
        fig_env_open += 1
    if '\\end{figure' in l:
        fig_env_open -= 1

print(f"\n7. Figure environment balance: {'BALANCED (0)' if fig_env_open == 0 else f'UNBALANCED ({fig_env_open})'}")
