import os
import zipfile

zip_path = r"C:\Users\umert\Downloads\aquavolt_mrv_unet_paper_overleaf.zip"
latex_dir = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk\paper_latex"

def main():
    print("[ZIP BUILDER] Creating final Overleaf package zip...")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
        # Copy main LaTeX files
        files_to_copy = ['sn-article.tex', 'sn-bibliography.bib', 'sn-jnl.cls', 'sn-mathphys-num.bst', 'sn-article.pdf']
        for f in files_to_copy:
            p = os.path.join(latex_dir, f)
            if os.path.exists(p):
                z.write(p, f)
                print(f"  + Added: {f}")
                
        # Copy figures subdirectory
        fig_dir = os.path.join(latex_dir, 'figures')
        if os.path.exists(fig_dir):
            for f in os.listdir(fig_dir):
                fp = os.path.join(fig_dir, f)
                if os.path.isfile(fp):
                    z.write(fp, os.path.join('figures', f))
                    print(f"  + Added: figures/{f}")
                    
    print(f"[SUCCESS] Final Overleaf package generated at: {zip_path}")

if __name__ == "__main__":
    main()
