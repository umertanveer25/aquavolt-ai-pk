import os

latex_file = r"C:\Users\umert\aquavolt-ai-pk\paper_latex\sn-article.tex"

with open(latex_file, "r", encoding="utf-8") as f:
    content = f.read()

# Add float package
if "\\usepackage{float}" not in content:
    content = content.replace("\\usepackage{graphicx}", "\\usepackage{graphicx}\n\\usepackage{float}")

# Replace the figure placement for system_architecture.png
target_block = r"""\begin{figure}[h]
\centering
\includegraphics[width=\textwidth]{figures/system_architecture.png}"""

replacement_block = r"""\begin{figure}[H]
\centering
\includegraphics[width=0.95\textwidth]{figures/system_architecture.png}"""

if target_block in content:
    content = content.replace(target_block, replacement_block)
else:
    # try softer match
    content = content.replace(r"\includegraphics[width=\textwidth]{figures/system_architecture.png}", r"\includegraphics[width=0.95\textwidth]{figures/system_architecture.png}")
    content = content.replace(r"\begin{figure}[h]", r"\begin{figure}[H]") # might replace all, which is fine to lock them down

with open(latex_file, "w", encoding="utf-8") as f:
    f.write(content)

print("Figure placement fixed to [H] and width scaled to 0.95.")
