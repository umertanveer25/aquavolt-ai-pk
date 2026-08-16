import re
import os

bib_path = r'C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-bibliography.bib'
with open(bib_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Match entries
entries = re.findall(r'@(\w+)\s*\{\s*([^,]+),\s*(.*?)\n\}', text, re.DOTALL)
print(f"Total entries matched: {len(entries)}")

catalog = []
for etype, key, body in entries:
    fields = {}
    for line in re.findall(r'(\w+)\s*=\s*\{([^}]*)\}', body, re.DOTALL):
        fields[line[0].lower()] = re.sub(r'\s+', ' ', line[1]).strip()
    catalog.append({
        'key': key.strip(),
        'type': etype.strip(),
        'title': fields.get('title', 'N/A'),
        'author': fields.get('author', 'N/A'),
        'year': fields.get('year', 'N/A'),
        'journal': fields.get('journal', fields.get('booktitle', fields.get('publisher', 'N/A'))),
        'volume': fields.get('volume', ''),
        'pages': fields.get('pages', ''),
        'doi': fields.get('doi', '')
    })

for i, c in enumerate(catalog, 1):
    print(f"{i:2d}. [{c['key']}] ({c['year']}) '{c['title']}' by {c['author'][:40]}... in {c['journal']}")
