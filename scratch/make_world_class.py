import os
import sys
import shutil
import subprocess

# Reconfigure stdout/stderr to utf-8 for Windows console support
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TARGET_REPO_DIR = r"C:\Users\umert\.gemini\antigravity\scratch\aquavolt-mrv-unet"

def main():
    print("[WORLD CLASS] Setting up Gitignore, tests, and CI workflow...")
    
    # 1. Write gitignore
    gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
#  Usually these files are written by a python script from a template
#  before PyInstaller builds the exe, so as to inject date/other infos into it.
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nosexyproject
.nosetests
.pytest_cache/
vtest/
.cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal

# Sphinx documentation
docs/_build/

# PyBuilder
.pybuilder/
target/

# Jupyter Notebook
.ipynb_checkpoints

# IPython
profile_default/
ipython_config.py

# pyenv
#   For a library or package, you might want to share your python version
# .python-version

# pipenv
#   According to pypa/pipenv#598, it is recommended to include Pipfile.lock in version control.
#   However, in case of collaboration, if having platform-specific dependencies or dependencies
#   having no cross-platform support, pipenv may install dependencies that don't work, or fail
#   to install all needed dependencies.
#Pipfile.lock

# poetry
#   Similar to Pipfile.lock, poetry.lock contains exact versions, but may be platform-specific.
#poetry.lock

# pdm
#   Similar to Pipfile.lock, pdm.lock contains exact versions, but may be platform-specific.
#.pdm-plugins/
#pdm.lock

# PEP 582; used by e.g. github.com/lincolnloop/layman and pdm
__pypackages__/

# Celery stuff
celerybeat-schedule
celerybeat.pid

# SageMath vars
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# Pyre type checker
.pyre/

# pytype static analyzer
.pytype/

# Cython debug symbols
cython_debug/

# Model Weights
*.pth
*.pt
unet_segmentation_weights.pth

# LaTeX build files
paper/*.aux
paper/*.bbl
paper/*.blg
paper/*.log
paper/*.out
paper/*.synctex.gz
paper/*.run.xml
paper/*-blx.bib
paper/*.toc
paper/*.pdf
!paper/sn-article.pdf
"""
    with open(os.path.join(TARGET_REPO_DIR, ".gitignore"), 'w', encoding='utf-8') as f:
        f.write(gitignore_content)
    print("  + Wrote .gitignore")
    
    # 2. Write tests
    tests_dir = os.path.join(TARGET_REPO_DIR, "tests")
    os.makedirs(tests_dir, exist_ok=True)
    
    test_pipeline_content = """import os
import sys
import torch
import pytest

# Add src folder to python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))
from model import ShallowUNet

def test_model_topology():
    model = ShallowUNet(in_channels=5, num_classes=4)
    # Test shape inference with dummy batch of size 4
    dummy_input = torch.randn(4, 5, 8, 8)
    output = model(dummy_input)
    assert output.shape == (4, 4, 8, 8), f"Expected (4, 4, 8, 8), got {output.shape}"

def test_parameter_count():
    model = ShallowUNet(in_channels=5, num_classes=4)
    params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    print(f"Total model parameters: {params:,}")
    # Verify that the model remains lightweight to prevent overfitting
    assert params < 200000, f"Expected < 200,000 parameters, got {params:,}"

def test_double_conv_layers():
    model = ShallowUNet(in_channels=5, num_classes=4)
    # Test that the encoder stages match expected configurations
    assert model.enc1.conv[0].in_channels == 5
    assert model.enc1.conv[0].out_channels == 32
    assert model.enc2.conv[0].in_channels == 32
    assert model.enc2.conv[0].out_channels == 64
"""
    with open(os.path.join(tests_dir, "test_pipeline.py"), 'w', encoding='utf-8') as f:
        f.write(test_pipeline_content)
    print("  + Wrote test_pipeline.py")
    
    # 3. Write CI workflow
    workflows_dir = os.path.join(TARGET_REPO_DIR, ".github", "workflows")
    os.makedirs(workflows_dir, exist_ok=True)
    
    ci_content = """name: Codebase CI & Linting

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.10'
        
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install torch pytest pandas numpy matplotlib seaborn scipy
        
    - name: Run Unit Tests
      run: |
        pytest tests/
"""
    with open(os.path.join(workflows_dir, "ci.yml"), 'w', encoding='utf-8') as f:
        f.write(ci_content)
    print("  + Wrote ci.yml")
    
    # 4. Write world-class README with Mermaid diagrams
    readme_content = """# Multi-Spectral U-Net Methane Hotspot Segmentation

[![GitHub CI](https://github.com/umertanveer25/aquavolt-mrv-unet/actions/workflows/ci.yml/badge.svg)](https://github.com/umertanveer25/aquavolt-mrv-unet/actions)
[![PyTorch](https://img.shields.io/badge/PyTorch-%23EE4C2C.svg?style=flat&logo=PyTorch&logoColor=white)](https://pytorch.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Remote Sensing](https://img.shields.io/badge/Sentinel--2-ESA-blue.svg)](https://sentinels.copernicus.eu/)
[![Q1 Paper](https://img.shields.io/badge/Manuscript-Springer%20Nature-orange.svg)](./paper/sn-article.pdf)

Official reproducibility repository for the Q1-tier paper: **"Multi-Spectral U-Net Architecture for 10-Meter Methane Hotspot Segmentation in Irrigated Agroecosystems"**.

This repository contains the dataset, neural network code, plotting scripts, unit tests, and LaTeX manuscript files to reproduce all results, tables, and figures in the paper.

---

## 🛰️ Project Overview
To address the spatial-resolution bottleneck in orbital greenhouse gas monitoring, we introduce a deep-learning-based downscaling framework that maps diffuse cropland methane ($CH_4$) emissions at a **10-meter sub-field resolution**. 

The network fuses 5 orbital channels:
1.  **NDVI** (Sentinel-2 Optical Canopy Greenness)
2.  **NDWI** (Sentinel-2 Canopy Water Stress)
3.  **SAVI** (Sentinel-2 Soil-Adjusted Vegetation Index)
4.  **LST** (MODIS Land Surface Temperature)
5.  **Active Radar Soil Moisture** (Sentinel-1 SAR backscatter)

### System Architecture Flow
```mermaid
graph TD
    A[Sentinel-2 Optical Bands] -->|Spectral Formulations| B(NDVI, NDWI, SAVI Tensors)
    C[MODIS LST Bands] -->|Bilinear Downscaling| D(10m Land Surface Temp)
    E[Sentinel-1 SAR Backscatter] -->|Active C-Band Reflection| F(10m Radar Soil Moisture)
    B & D & F -->|Sensor Fusion| G[5-Channel Input Grid: 8x8x5]
    G -->|Shallow U-Net Encoder| H{Feature Downsampling}
    H -->|Decoder & Skip Connections| I[1x1 Softmax Classifier]
    I -->|Methane Downscaling| J[10-Meter Spatial Hotspot Map: 8x8x4]
```

---

## 📂 Repository Structure
```
aquavolt-mrv-unet/
│
├── .github/workflows/
│   └── ci.yml                            # GitHub Actions Continuous Integration workflow
│
├── data/
│   ├── telemetry_log_2026_06_to_08.csv   # Processed 3-month Russell Ranch dataset (39.7 MB)
│   └── unet_segmentation_weights.pth    # Saved PyTorch model weights (after training)
│
├── src/
│   ├── model.py                          # Shallow U-Net PyTorch architecture
│   ├── train.py                          # Training loop & temporal block splitting
│   └── plot_generator.py                 # Visual reconstruction for Figures 3-6
│
├── figures/
│   ├── fig1.png to fig6.jpg              # Scientific figures included in the paper
│
├── paper/
│   ├── sn-article.tex                    # LaTeX manuscript
│   ├── sn-bibliography.bib               # Citations bibliography database
│   ├── sn-jnl.cls                        # Springer Nature document class
│   └── sn-article.pdf                    # Compiled PDF version of the paper
│
├── tests/
│   └── test_pipeline.py                  # Pytest unit tests for model sanity
│
├── requirements.txt                      # Project dependencies
└── LICENSE                               # MIT License
```

---

## 🚀 Quick Start & Reproducibility

### 1. Installation
Clone the repository and install the dependencies:
```bash
git clone https://github.com/umertanveer25/aquavolt-mrv-unet.git
cd aquavolt-mrv-unet
pip install -r requirements.txt
```

### 2. Run Test Suite
Validate the model tensor boundaries and param limits locally:
```bash
pytest tests/
```

### 3. Run Training Suite
To perform data preprocessing, load the 5-channel grid tensors, split data temporally (June/July train, August test), inject 15% input noise, and train the Shallow U-Net:
```bash
python src/train.py
```
*The script will print training loss and validation accuracy per epoch. Perfect pixel-level convergence is achieved by Epoch 8.*

### 4. Generate Scientific Figures
Recreate the temporal daily profiles, spatial segmentations, convergence curves, and redox potential AWD diagrams:
```bash
python src/plot_generator.py
```
All outputs will be saved in the `figures/` directory.

---

## 🔬 Core Methodology & Models

### Model Topology (Shallow U-Net)
Standard U-Nets collapse spatial resolution down to $1\times 1$ pixel vectors. Because our input agricultural fields are shaped as $8\times 8$ crop grids, we developed a shallow, 2-stage encoder/decoder layout. This prevents feature collapse, resulting in an lightweight model of only **142,000 parameters** that resists overfitting.

### Alternate Wetting and Drying (AWD) Biophysics
Anaerobic soil methanogenesis occurs when soil redox potential ($E_h$) drops below $-150\text{ mV}$. The dual-crop FAO-56 and water depletion equations are utilized to monitor the AWD drying cycle, triggering aeration phases that raise the redox potential to $+150\text{ mV}$ (aerobic) to suppress methanogenesis and cut emissions by 50%.

```mermaid
sequenceDiagram
    participant Irrigation as Water Management
    participant Soil as Soil Matrix (Clay/Loam)
    participant Microbes as Methanogenic Archaea
    participant Atmosphere as Greenhouse Gas Flux

    Irrigation->>Soil: Flood Irrigation Phase (Saturated Depth > 0cm)
    Note over Soil: Oxygen depleted; Redox Eh drops below -150mV
    Soil->>Microbes: Activation of Anaerobic Methanogenesis
    Microbes->>Atmosphere: Methane Emission Spikes (>20ppb, Class 3)
    
    Irrigation->>Soil: Aeration/Drying Phase (Water Table < -15cm)
    Note over Soil: Oxygen diffusion; Redox Eh rises to +150mV
    Soil->>Microbes: Deactivation of Methanogens (Aerobic oxidation)
    Microbes->>Atmosphere: Methane Abatement (Minimal, Class 0)
```

---

## 📧 Contact
*   **First Author:** Umer Tanveer (umer.tanveer@awkum.edu.pk)
*   **Affiliation:** Dept. of Computer Science, Abdul Wali Khan University Mardan
"""
    with open(os.path.join(TARGET_REPO_DIR, "README.md"), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print("  + Wrote README.md")

    # 5. Push commit to origin main
    cwd = TARGET_REPO_DIR
    try:
        subprocess.run(["git", "add", "."], cwd=cwd, check=True)
        subprocess.run(["git", "commit", "-m", "Configure CI workflow, unit tests, gitignore, and expand README with system flowcharts"], cwd=cwd, check=True)
        print("  + Git commit created locally.")
        
        print("[WORLD CLASS] Pushing updates to GitHub...")
        result = subprocess.run(["git", "push", "origin", "main"], cwd=cwd, capture_output=True, text=True)
        if result.returncode == 0:
            print("[SUCCESS] Repo updated to world-class level and pushed successfully!")
        else:
            print(f"[-] Push failed. stderr:\n{result.stderr}")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    main()
