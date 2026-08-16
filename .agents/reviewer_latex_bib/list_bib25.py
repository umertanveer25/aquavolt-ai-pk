import os
import re

bib_path = r'C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-bibliography.bib'
with open(bib_path, 'r', encoding='utf-8') as f:
    text = f.read()

entries = re.findall(r'@(\w+)\s*\{\s*([^,]+),\s*(.*?)\n\}', text, re.DOTALL)
print(f"Total entries: {len(entries)}")

for idx, (etype, key, body) in enumerate(entries[:25], 1):
    fmatches = re.findall(r'(\w+)\s*=\s*[\{"](.*?)[}"]\s*(?:,|$)', body, re.DOTALL)
    fdict = {k.lower(): v.strip().replace('\n', ' ') for k, v in fmatches}
    author = fdict.get('author', 'NO AUTHOR')[:30]
    year = fdict.get('year', 'NO YEAR')
    title = fdict.get('title', 'NO TITLE')[:50]
    journal = fdict.get('journal', fdict.get('booktitle', fdict.get('publisher', 'NO VENUE')))[:30]
    print(f"{idx:02d}. [{key}] ({year}) {author} | {title} | {journal}")
