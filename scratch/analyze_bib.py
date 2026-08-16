import os
import sys
import re

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

bib_path = r"C:\Users\umert\.gemini\antigravity\brain\3924f3fd-e810-4763-a571-e7315616bc0e\references.bib"

if not os.path.exists(bib_path):
    print("[-] Bibliography file not found!")
    exit(1)

content = open(bib_path, encoding='utf-8').read()

# Match BibTeX entries and extract titles
entries = re.findall(r'@\w+\{(.*?),', content)
titles = re.findall(r'title\s*=\s*[\"{]((?:.|\n)*?)[\"}],', content, re.IGNORECASE)

print(f"Total BibTeX Entries Found: {len(entries)}")
print(f"Total Extracted Titles: {len(titles)}")

# Clean titles (remove curly braces and newlines)
clean_titles = [re.sub(r'[\{\}\n\r\s]+', ' ', t).strip() for t in titles]

methane_count = 0
cv_count = 0
agri_count = 0
other_count = 0

print("\n--- SAMPLE TITLES & RELEVANCE CLASSIFICATION ---")
for idx, title in enumerate(clean_titles[:25]):
    low_title = title.lower()
    is_methane = 'methane' in low_title or 'ch4' in low_title
    is_cv = any(w in low_title for w in ['segment', 'net', 'deep', 'learning', 'cnn', 'transformer', 'attention', 'unet'])
    is_agri = any(w in low_title for w in ['soil', 'moisture', 'water', 'crop', 'agri', 'irrigate', 'cimis', 'evapo', 'vegetation', 'flux'])
    
    relevance = []
    if is_methane:
        relevance.append("Methane")
        methane_count += 1
    if is_cv:
        relevance.append("Computer Vision")
        cv_count += 1
    if is_agri:
        relevance.append("Agriculture/Hydrology")
        agri_count += 1
        
    rel_str = " + ".join(relevance) if relevance else "Other/General"
    if not relevance:
        other_count += 1
        
    print(f"{idx+1}. {title[:60]}... [{rel_str}]")

# Count remaining titles
for title in clean_titles[25:]:
    low_title = title.lower()
    is_methane = 'methane' in low_title or 'ch4' in low_title
    is_cv = any(w in low_title for w in ['segment', 'net', 'deep', 'learning', 'cnn', 'transformer', 'attention', 'unet'])
    is_agri = any(w in low_title for w in ['soil', 'moisture', 'water', 'crop', 'agri', 'irrigate', 'cimis', 'evapo', 'vegetation', 'flux'])
    
    if is_methane: methane_count += 1
    if is_cv: cv_count += 1
    if is_agri: agri_count += 1
    if not (is_methane or is_cv or is_agri): other_count += 1

print("\n--- FINAL COUNTS ---")
print(f"Methane-related: {methane_count}")
print(f"Computer Vision/Deep Learning-related: {cv_count}")
print(f"Agriculture/Hydrology-related: {agri_count}")
print(f"Other/General Remote Sensing: {other_count}")
