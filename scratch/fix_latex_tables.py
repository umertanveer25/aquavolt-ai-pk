import os
import re

p = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.tex"

def main():
    print("[TABLE FIXER] Loading sn-article.tex...")
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Let's split by \begin{table*}[htbp] and \end{table*} to isolate each table block
    table_pattern = re.compile(r"(\\begin\{table\*\}\[htbp\].*?\\end\{table\*\})", re.DOTALL)
    blocks = table_pattern.split(content)
    
    table_index = 0
    new_blocks = []
    
    for block in blocks:
        if block.startswith(r"\begin{table*}[htbp]"):
            table_index += 1
            print(f"  + Processing Table {table_index}...")
            
            if table_index == 1:
                # Table 1: Ingestion metadata (long text)
                block = block.replace(
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llllll@{}}",
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}p{2.6cm}p{3.2cm}p{1.5cm}p{1.2cm}p{3.8cm}p{3.8cm}@{}}"
                )
            elif table_index == 2:
                # Table 2: Model hyperparameters (medium text)
                block = block.replace(
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lllll@{}}",
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}p{2.2cm}p{4cm}p{2.2cm}p{3.2cm}p{4.8cm}@{}}"
                )
            elif table_index == 3:
                # Table 3: Performance benchmark (numeric, 9 columns) -> Resize
                block = block.replace(
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccccc@{}}",
                    r"\resizebox{\textwidth}{!}{%" + "\n" + r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccccc@{}}"
                )
                block = block.replace(
                    r"\end{tabular*}",
                    r"\end{tabular*}" + "\n" + r"}"
                )
            elif table_index == 4:
                # Table 4: Methane downscaling comparison (medium text, 7 columns)
                block = block.replace(
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccc@{}}",
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}p{3.2cm}cccccp{3.8cm}@{}}"
                )
            elif table_index == 5:
                # Table 5: Ablation study (numeric, 7 columns) -> Resize
                block = block.replace(
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccc@{}}",
                    r"\resizebox{\textwidth}{!}{%" + "\n" + r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccc@{}}"
                )
                block = block.replace(
                    r"\end{tabular*}",
                    r"\end{tabular*}" + "\n" + r"}"
                )
            elif table_index == 6:
                # Table 6: Statistical tests (numeric, 7 columns) -> Resize
                block = block.replace(
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccc@{}}",
                    r"\resizebox{\textwidth}{!}{%" + "\n" + r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccc@{}}"
                )
                block = block.replace(
                    r"\end{tabular*}",
                    r"\end{tabular*}" + "\n" + r"}"
                )
            elif table_index == 7:
                # Table 7: SOTA literature comparison (long text, 6 columns)
                block = block.replace(
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}llllll@{}}",
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}p{2.6cm}p{3cm}p{3.2cm}p{2.2cm}p{2.2cm}p{3.2cm}@{}}"
                )
            elif table_index == 8:
                # Table 8: Soil and crop parameter matrix (numeric, 9 columns) -> Resize
                block = block.replace(
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccccc@{}}",
                    r"\resizebox{\textwidth}{!}{%" + "\n" + r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lcccccccc@{}}"
                )
                block = block.replace(
                    r"\end{tabular*}",
                    r"\end{tabular*}" + "\n" + r"}"
                )
            elif table_index == 9:
                # Table 9: Edge hardware benchmarks (numeric, 7 columns) -> Resize
                block = block.replace(
                    r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lllllll@{}}",
                    r"\resizebox{\textwidth}{!}{%" + "\n" + r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}lllllll@{}}"
                )
                block = block.replace(
                    r"\end{tabular*}",
                    r"\end{tabular*}" + "\n" + r"}"
                )
            
            new_blocks.append(block)
        else:
            new_blocks.append(block)
            
    # Write back
    new_content = "".join(new_blocks)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print("[SUCCESS] All tables modified in sn-article.tex!")

if __name__ == "__main__":
    main()
