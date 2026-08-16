import os
import sys
import shutil
import subprocess

# Reconfigure stdout/stderr to utf-8 for Windows console support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

PROJECT_DIR = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-ai-pk"
ART_DIR = r"C:\Users\umert\.gemini\antigravity\brain\3924f3fd-e810-4763-a571-e7315616bc0e"
FIG_DEST_DIR = os.path.join(PROJECT_DIR, "paper_latex", "figures")

FIG_MAPPINGS = {
    "fig1.png": "unet_system_flowchart_1786650121100.jpg",
    "fig2.png": "study_area_grid_map_1786650180833.jpg",
    "fig3.png": "temporal_feature_profiles_1786650207581.jpg",
    "fig4.png": "spatial_segmentation_comparison_1786650232224.jpg",
    "fig5.png": "unet_training_convergence_1786650257256.jpg"
}

def main():
    print("[FIG SYNC] Syncing correct U-Net crop stress figures...")
    
    # Try importing PIL to convert format properly
    try:
        from PIL import Image
        pil_available = True
        print("  + PIL is available. Will convert JPG to actual PNG format.")
    except ImportError:
        pil_available = False
        print("  [-] PIL not found. Will copy bytes directly (pdflatex supports this).")
        
    for dest_name, src_name in FIG_MAPPINGS.items():
        src_path = os.path.join(ART_DIR, src_name)
        dest_path = os.path.join(FIG_DEST_DIR, dest_name)
        
        if os.path.exists(src_path):
            if pil_available:
                img = Image.open(src_path)
                img.save(dest_path, "PNG")
                print(f"  + Converted {src_name} -> {dest_name}")
            else:
                shutil.copy2(src_path, dest_path)
                print(f"  + Copied {src_name} -> {dest_name} directly")
        else:
            print(f"  [-] Source figure {src_name} not found in {ART_DIR}")
            
    # Also sync fig6.jpg from art dir to paper_latex/figures/ if missing
    fig6_src = os.path.join(ART_DIR, "fig6.jpg")
    fig6_dest = os.path.join(FIG_DEST_DIR, "fig6.jpg")
    if os.path.exists(fig6_src):
        shutil.copy2(fig6_src, fig6_dest)
        print("  + Synced fig6.jpg")
        
    # Re-run LaTeX compilation to generate the PDF with the correct images
    print("[FIG SYNC] Re-compiling LaTeX paper with the correct figures...")
    latex_dir = os.path.join(PROJECT_DIR, "paper_latex")
    try:
        # Run pdflatex
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "sn-article.tex"], cwd=latex_dir, check=True)
        print("[FIG SYNC] pdflatex pass 1 complete.")
        # Run bibtex
        subprocess.run(["bibtex", "sn-article"], cwd=latex_dir, check=True)
        print("[FIG SYNC] bibtex complete.")
        # Run pdflatex x2 to resolve citations and page layout
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "sn-article.tex"], cwd=latex_dir, check=True)
        subprocess.run(["pdflatex", "-interaction=nonstopmode", "sn-article.tex"], cwd=latex_dir, check=True)
        print("[SUCCESS] PDF compiled successfully with the correct figures!")
    except Exception as e:
        print(f"[-] LaTeX compilation failed: {e}")

if __name__ == "__main__":
    main()
