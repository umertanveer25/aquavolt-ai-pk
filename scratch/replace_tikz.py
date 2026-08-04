import os
import re

latex_file = r"C:\Users\umert\aquavolt-ai-pk\paper_latex\sn-article.tex"

with open(latex_file, "r", encoding="utf-8") as f:
    content = f.read()

# Replace the TikZ block with includegraphics
pattern = re.compile(r"\\begin\{tikzpicture\}.*?\\end\{tikzpicture\}", re.DOTALL)
replacement = r"\\includegraphics[width=\\textwidth]{figures/system_architecture.png}"

content = re.sub(pattern, replacement, content)

with open(latex_file, "w", encoding="utf-8") as f:
    f.write(content)

print("TikZ replaced with includegraphics for system_architecture.png")
