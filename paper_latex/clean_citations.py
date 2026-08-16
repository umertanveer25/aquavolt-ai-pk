# Update generate_full_manuscript.py to cleanly map only the verified 76 keys

import os
import re

with open('paper_latex/generate_full_manuscript.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace the 3 extra keys with verified keys from the 76
text = text.replace(',Pepin2022', '')
text = text.replace(',Boulton2022', '')
text = text.replace('Forzieri2022,', '')

with open('paper_latex/generate_full_manuscript.py', 'w', encoding='utf-8') as f:
    f.write(text)

print("Updated generate_full_manuscript.py")
