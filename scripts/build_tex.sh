#!/bin/bash
# Scripts to generate and build TeX dictionary
set -e

# Change to project root if script is run from scripts/
cd "$(dirname "$0")/.."

# 1. Generate TeX files
echo "Generating TeX files..."
source .venv/bin/activate
python3 scripts/generate_tex_dict.py

# 2. Compile if XeLaTeX is available
if command -v xelatex >/dev/null 2>&1; then
    echo "XeLaTeX found. Compiling main.tex..."
    cd artifacts/tex
    # Run twice to resolve TOC
    xelatex -interaction=batchmode main.tex >/dev/null
    xelatex -interaction=batchmode main.tex >/dev/null
    echo "PDF generated at artifacts/tex/main.pdf"
else
    echo "XeLaTeX not found. TeX files are available in artifacts/tex/"
fi
