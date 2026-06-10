---
id: doc-10
title: Modular Dictionary Print Pipeline Guide
type: guide
created_date: '2026-06-10 16:18'
---# Modular Dictionary Print Pipeline Guide

This technical guide summarizes the print pipeline designed to transform a structured datasheet into a professionally typeset print dictionary using a modular LaTeX architecture.

---

## 1. Technical Stack Summary

### A. Data Processing & Generation
- **Python**: Primary engine for the pipeline. Ingests datasheets (CSV/JSON), sanitizes text, and programmatically generates LaTeX source files.
- **pylatexenc & PyLaTeX**: Handles escaping special characters and Unicode glyphs—critical for maintaining endangered language diacritics—while wrapping data in semantic LaTeX macros.

### B. Typesetting & Layout
- **XeLaTeX**: Typesetting engine that natively supports OpenType fonts and Unicode, ensuring unique Cherokee/linguistic characters render perfectly.
- **Modular Architecture (`\include`)**: Splits the dictionary into hundreds of small `.tex` files organized by word root, allowing rapid recompilation of specific sections and preventing Git merge conflicts.

### C. Build & Version Management
- **Git**: Every generated root file and the master configuration is tracked in source control, providing clear history and rollbacks.
- **Build Entry Point**: Implemented in the [tex_dictionary](../../../../tex_dictionary/) module. Run it using:
  ```bash
  python3 -m tex_dictionary
  ```

---

## 2. Workflow Overview

1. **Generate**: Run `python3 -m tex_dictionary`.
2. **Extract**: The generator in [generator.py](../../../../tex_dictionary/generator.py) reads `hierarchical-dict.json` and `underlying_stems.csv`.
3. **Structure**: Individual `.tex` snippet files are created for each root in `artifacts/tex/roots/`.
4. **Stitch**: A master `main.tex` file pulls these snippets together.
5. **Compile**: If `xelatex` is available, it produces a print-ready PDF at `artifacts/tex/main.pdf`.

---

## 3. Font Requirements

- The current template uses **Plantagenet Cherokee**, which is standard on macOS and provides excellent support for both Latin and Cherokee characters.
