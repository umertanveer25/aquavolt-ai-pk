import os
import re

with open('paper_latex/generate_full_manuscript.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Remove \usepackage[title]{appendix} to avoid clash with sn-jnl.cls
text = text.replace(r'\usepackage[title]{appendix}', '% appendix handled natively by sn-jnl')

# Fix listings language=json to standard verbatim listings
text = text.replace(r'\begin{lstlisting}[language=json]', r'\begin{lstlisting}')

# Ensure enumerate in Appendix C is formatted cleanly
text = text.replace(r'\begin{enumerate}', r'\begin{itemize}')
text = text.replace(r'\end{enumerate}', r'\end{itemize}')

with open('paper_latex/generate_full_manuscript.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed generate_full_manuscript.py")
