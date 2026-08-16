import sys

PDF_FILE = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.pdf"

try:
    import pypdf
    reader = pypdf.PdfReader(PDF_FILE)
    print("pypdf installed. Number of pages:", len(reader.pages))
    print("Title / Metadata:", reader.metadata)
except Exception as e:
    print("pypdf check failed/not installed:", e)

try:
    import PyPDF2
    reader = PyPDF2.PdfReader(PDF_FILE)
    print("PyPDF2 installed. Number of pages:", len(reader.pages))
except Exception as e:
    print("PyPDF2 check failed/not installed:", e)

