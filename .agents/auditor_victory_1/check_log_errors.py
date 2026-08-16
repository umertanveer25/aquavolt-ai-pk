LOG_FILE = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.log"

with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

print(f"Total lines in log: {len(lines)}")
for i, line in enumerate(lines):
    if "error" in line.lower() or line.startswith("!"):
        print(f"Line {i+1}: {line.strip()}")

