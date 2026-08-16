import re

TEX_PATH = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.tex"

with open(TEX_PATH, 'r', encoding='utf-8') as f:
    content = f.read()

# Find all \begin{...}
begins = re.findall(r'\\begin\{([a-zA-Z*]+)\}', content)
from collections import Counter
print("Environment counts:", Counter(begins))

# Find all \label{...}
labels = re.findall(r'\\label\{([^}]+)\}', content)
print("\nLabels found:")
for l in sorted(labels):
    print(" ", l)

# Find all figure inclusions and captions
print("\nFigures and Captions:")
fig_blocks = re.findall(r'(\\begin\{figure\*?\}.*?\\end\{figure\*?\})', content, re.DOTALL)
print(f"Total figure blocks found: {len(fig_blocks)}")
for i, fb in enumerate(fig_blocks, 1):
    cap = re.search(r'\\caption\{([^}]+)\}', fb)
    lbl = re.search(r'\\label\{([^}]+)\}', fb)
    ig = re.search(r'\\includegraphics(\[[^\]]*\])?\{([^}]+)\}', fb)
    print(f"\n--- Figure Block {i} ---")
    print("Label:", lbl.group(1) if lbl else "NO LABEL")
    print("Graphics:", ig.group(2) if ig else "NO GRAPHICS")
    print("Caption:", cap.group(1)[:100] if cap else "NO CAPTION")

# Find all table inclusions and captions
print("\nTables and Captions:")
tab_blocks = re.findall(r'(\\begin\{table\*?\}.*?\\end\{table\*?\})', content, re.DOTALL)
print(f"Total table blocks found: {len(tab_blocks)}")
for i, tb in enumerate(tab_blocks, 1):
    cap = re.search(r'\\caption\{([^}]+)\}', tb)
    lbl = re.search(r'\\label\{([^}]+)\}', tb)
    print(f"\n--- Table Block {i} ---")
    print("Label:", lbl.group(1) if lbl else "NO LABEL")
    print("Caption:", cap.group(1)[:100] if cap else "NO CAPTION")

