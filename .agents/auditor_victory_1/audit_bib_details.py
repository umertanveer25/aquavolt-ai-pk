import re
import json

BIB_PATH = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-bibliography.bib"
TEX_PATH = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.tex"

with open(BIB_PATH, "r", encoding="utf-8") as f:
    bib_text = f.read()

with open(TEX_PATH, "r", encoding="utf-8") as f:
    tex_text = f.read()

# Parse bib entries
entries = re.findall(r'@(\w+)\s*\{\s*([^,\s]+)\s*,\s*(.*?)\n\}\s*(?=@|\Z)', bib_text, re.DOTALL)
print(f"Total parsed bib entries: {len(entries)}")

bib_summary = []
for entry_type, key, body in entries:
    title_m = re.search(r'title\s*=\s*[\{"](.*?)[\}"]', body, re.IGNORECASE | re.DOTALL)
    author_m = re.search(r'author\s*=\s*[\{"](.*?)[\}"]', body, re.IGNORECASE | re.DOTALL)
    year_m = re.search(r'year\s*=\s*[\{"]?(\d{4})[\}"]?', body, re.IGNORECASE)
    
    title = title_m.group(1).replace('\n', ' ').strip() if title_m else "NO TITLE"
    author = author_m.group(1).replace('\n', ' ').strip() if author_m else "NO AUTHOR"
    year = year_m.group(1) if year_m else "NO YEAR"
    
    # Check citation count in TeX
    cites = len(re.findall(rf'\\cite[a-zA-Z]*\{{[^}}]*\b{re.escape(key)}\b[^}}]*\}}', tex_text))
    
    bib_summary.append({
        "key": key,
        "type": entry_type,
        "author": author[:50],
        "title": title[:60],
        "year": year,
        "cited_in_tex_count": cites
    })

print("\nBib Entries Summary (First 15):")
for b in bib_summary[:15]:
    print(f"[{b['key']}] ({b['year']}) cites={b['cited_in_tex_count']} | {b['author']} | {b['title']}")

uncited = [b for b in bib_summary if b['cited_in_tex_count'] == 0]
print(f"\nTotal uncited entries in TeX: {len(uncited)}")
if uncited:
    print("Uncited entries:", [u['key'] for u in uncited])

with open(r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\.agents\auditor_victory_1\bib_audit.json", "w") as f:
    json.dump(bib_summary, f, indent=2)
print("Saved bib audit to bib_audit.json")
