import os
import re

p = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-bibliography.bib"

def main():
    print("[BIB CHECK] Reading sn-bibliography.bib...")
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Split entries by @
    entries = content.split('@')
    valid_entries = []
    
    for entry in entries:
        if not entry.strip():
            continue
            
        # Parse type and key
        match_key = re.match(r'^([a-zA-Z]+)\{([^,]+),', entry.strip())
        if match_key:
            entry_type = match_key.group(1)
            key = match_key.group(2)
            
            # Find title
            title_match = re.search(r'title\s*=\s*[\"{]?(.*?)[\"}]?,?$', entry, re.IGNORECASE | re.MULTILINE)
            title = ""
            if title_match:
                title = title_match.group(1).strip()
                # Clean up brackets
                title = re.sub(r'[\{\}\"]', '', title)
                
            # Find year
            year_match = re.search(r'year\s*=\s*[\"{]?(\d{4})[\"}]?', entry, re.IGNORECASE)
            year = ""
            if year_match:
                year = year_match.group(1)
                
            valid_entries.append((key, year, title))
            
    print(f"Total entries parsed: {len(valid_entries)}")
    for i, (key, year, title) in enumerate(valid_entries):
        print(f"{i+1:02d}. [{key}] ({year}) - {title[:100]}")

if __name__ == "__main__":
    main()
