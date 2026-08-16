import os
import subprocess
import re
import sys

LATEX_DIR = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex"
PDF_FILE = os.path.join(LATEX_DIR, "sn-article.pdf")
LOG_FILE = os.path.join(LATEX_DIR, "sn-article.log")
BLG_FILE = os.path.join(LATEX_DIR, "sn-article.blg")

print("--- STEP 1: CLEANING INTERMEDIATE FILES (except .tex and .bib) ---")
for ext in [".aux", ".bbl", ".blg", ".log", ".out", ".toc", ".synctex.gz"]:
    fpath = os.path.join(LATEX_DIR, "sn-article" + ext)
    if os.path.exists(fpath):
        try:
            os.remove(fpath)
            print(f"Removed {ext}")
        except Exception as e:
            print(f"Could not remove {ext}: {e}")

print("\n--- STEP 2: RUNNING PASS 1 (pdflatex) ---")
p1 = subprocess.run(["pdflatex", "-interaction=nonstopmode", "sn-article.tex"], cwd=LATEX_DIR, capture_output=True, text=True)
print(f"Pass 1 Return Code: {p1.returncode}")

print("\n--- STEP 3: RUNNING BIBTEX ---")
pb = subprocess.run(["bibtex", "sn-article"], cwd=LATEX_DIR, capture_output=True, text=True)
print(f"BibTeX Return Code: {pb.returncode}")
print("BibTeX STDOUT snippet:\n", pb.stdout[:500])
if pb.stderr:
    print("BibTeX STDERR:\n", pb.stderr)

print("\n--- STEP 4: RUNNING PASS 2 (pdflatex) ---")
p2 = subprocess.run(["pdflatex", "-interaction=nonstopmode", "sn-article.tex"], cwd=LATEX_DIR, capture_output=True, text=True)
print(f"Pass 2 Return Code: {p2.returncode}")

print("\n--- STEP 5: RUNNING PASS 3 (pdflatex) ---")
p3 = subprocess.run(["pdflatex", "-interaction=nonstopmode", "sn-article.tex"], cwd=LATEX_DIR, capture_output=True, text=True)
print(f"Pass 3 Return Code: {p3.returncode}")

print("\n--- STEP 6: VERIFYING COMPILER LOG ---")
with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
    log_content = f.read()

# Check for fatal errors
fatal_errors = re.findall(r'! .+', log_content)
print(f"Fatal errors in log: {len(fatal_errors)}")
for err in fatal_errors:
    print("  ", err)

# Check for undefined citations
undef_cites = re.findall(r'LaTeX Warning: Citation `([^`\']+)\' on page \d+ undefined', log_content)
print(f"Undefined citations in log: {len(undef_cites)}")
for uc in undef_cites:
    print("  Undefined cite:", uc)

# Check for undefined references
undef_refs = re.findall(r'LaTeX Warning: Reference `([^`\']+)\' on page \d+ undefined', log_content)
print(f"Undefined references in log: {len(undef_refs)}")
for ur in undef_refs:
    print("  Undefined ref:", ur)

# Check output pages in log
pages_match = re.search(r'Output written on sn-article\.pdf \((\d+) pages', log_content)
if pages_match:
    page_count = int(pages_match.group(1))
    print(f"LOG: Total pages written: {page_count}")
else:
    print("Could not find page count in log.")
    page_count = 0

print(f"\n--- STEP 7: PDF FILE CHECK ---")
if os.path.exists(PDF_FILE):
    size_mb = os.path.getsize(PDF_FILE) / (1024 * 1024)
    print(f"PDF exists: {PDF_FILE} ({size_mb:.2f} MB)")
else:
    print(f"ERROR: PDF file not found at {PDF_FILE}")

