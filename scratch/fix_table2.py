import os
import zipfile
import subprocess

p = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex\sn-article.tex"
zip_path = r"C:\Users\umert\Downloads\aquavolt_mrv_unet_paper_overleaf.zip"
latex_dir = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex"

def main():
    print("[TABLE 2 FIXER] Loading sn-article.tex...")
    with open(p, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Locate Table 2 block specifically by label
    target_start = r"\label{tab:model_hyperparams}"
    
    # We want to find the next \begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}p{2.2cm}p{4cm}p{2.2cm}p{3.2cm}p{4.8cm}@{}}" after the label
    tabular_start = r"\begin{tabular*}{\textwidth}{@{\extracolsep{\fill}}p{2.2cm}p{4cm}p{2.2cm}p{3.2cm}p{4.8cm}@{}}"
    
    # Let's do exact string replacement to wrap it in \resizebox
    old_fragment = target_start + "\n" + tabular_start
    new_fragment = target_start + "\n" + r"\resizebox{\textwidth}{!}{%" + "\n" + tabular_start
    
    if old_fragment in content:
        content = content.replace(old_fragment, new_fragment)
        
        # Now find the next \end{tabular*} and replace with \end{tabular*}%
        # Wait, since there are multiple \end{tabular*} in the file, we should search for the one right after the optimization block
        opt_block = r"$\lambda_{\text{upper}} = 10.0, \lambda_{\text{lower}} = 10.0, K_{c,\max} = 1.20$ \\"
        old_end = opt_block + "\n" + r"\botrule" + "\n" + r"\end{tabular*}"
        new_end = opt_block + "\n" + r"\botrule" + "\n" + r"\end{tabular*}" + "\n" + r"}"
        
        if old_end in content:
            content = content.replace(old_end, new_end)
            print("  + Table 2 successfully wrapped in \\resizebox!")
        else:
            # Alternate search with diff spacing
            old_end_alt = opt_block + "\r\n" + r"\botrule" + "\r\n" + r"\end{tabular*}"
            new_end_alt = opt_block + "\r\n" + r"\botrule" + "\r\n" + r"\end{tabular*}" + "\r\n" + r"}"
            if old_end_alt in content:
                content = content.replace(old_end_alt, new_end_alt)
                print("  + Table 2 successfully wrapped in \\resizebox (Windows line endings)!")
            else:
                print("  [-] Could not find ending marker of Table 2!")
    else:
        print("  [-] Could not find starting marker of Table 2!")
        
    # Write back
    with open(p, 'w', encoding='utf-8') as f:
        f.write(content)
        
    # Compile
    print("[TABLE 2 FIXER] Compiling LaTeX paper...")
    try:
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "sn-article.tex"], cwd=latex_dir, check=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "sn-article.tex"], cwd=latex_dir, check=True)
        print("[SUCCESS] LaTeX compiled successfully after wrapping Table 2!")
    except Exception as e:
        print(f"[-] Compilation failed: {e}")
        
    # Rebuild Zip in Downloads
    print("[TABLE 2 FIXER] Rebuilding Downloads ZIP...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        files_to_copy = ['sn-article.tex', 'sn-bibliography.bib', 'sn-jnl.cls', 'sn-mathphys-num.bst', 'sn-article.pdf']
        for f in files_to_copy:
            fp = os.path.join(latex_dir, f)
            if os.path.exists(fp):
                z.write(fp, f)
        fig_dir = os.path.join(latex_dir, 'figures')
        if os.path.exists(fig_dir):
            for f in os.listdir(fig_dir):
                fp = os.path.join(fig_dir, f)
                if os.path.isfile(fp):
                    z.write(fp, os.path.join('figures', f))
    print("[SUCCESS] Downloads ZIP updated!")

if __name__ == "__main__":
    main()
