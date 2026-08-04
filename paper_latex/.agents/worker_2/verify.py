import sys
import fitz # PyMuPDF

def verify():
    print("=== VERIFYING LATEX BUILD & OUTPUT ===")
    
    # 1. Check sn-article.log for Overfull \hbox
    overfulls = []
    with open(r"C:\Users\umert\aquavolt-ai-pk\paper_latex\sn-article.log", "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            if "Overfull \\hbox" in line:
                overfulls.append(line.strip())
    
    print(f"Overfull \\hbox count: {len(overfulls)}")
    for o in overfulls:
        print(f"  - {o}")
        
    # 2. Check PDF text for ???
    doc = fitz.open(r"C:\Users\umert\aquavolt-ai-pk\paper_latex\sn-article.pdf")
    pages_with_qmark = []
    for i, page in enumerate(doc):
        text = page.get_text()
        if "???" in text:
            pages_with_qmark.append(i + 1)
            
    print(f"Page count: {len(doc)}")
    print(f"Pages with ???: {pages_with_qmark}")
    
    # 3. Check reference [4] specifically
    ref_page = doc[15].get_text() if len(doc) >= 16 else ""
    print("--- Page 16 snippet (References) ---")
    for line in ref_page.splitlines():
        if "Allen" in line or "[4]" in line or "FAO" in line:
            print(line)
            
    if len(overfulls) == 0 and len(pages_with_qmark) == 0:
        print("\nSUCCESS: Zero Overfull \\hbox, Zero ??? placeholders!")
    else:
        print("\nFAILURE: Issues detected.")

if __name__ == "__main__":
    verify()
