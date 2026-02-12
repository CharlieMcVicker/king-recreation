## Technical Stack Summary: Modular Dictionary Print Pipeline

This technical stack is designed to transform a structured datasheet into a professionally typeset print dictionary, using a modular "root-based" architecture to ensure scalability and ease of collaboration through source control.

### 1. Data Processing & Generation

- **Python:** Acts as the primary engine for the pipeline. It will be used to ingest the datasheet (CSV/JSON), sanitize the text, and programmatically generate LaTeX source files.
- **pylatexenc & PyLaTeX:** These libraries will handle the heavy lifting of escaping special characters and Unicode glyphs—critical for maintaining the integrity of endangered language diacritics—while wrapping data in semantic LaTeX macros.

### 2. Typesetting & Layout

- **XeLaTeX:** The chosen typesetting engine. Unlike standard LaTeX, XeLaTeX natively supports OpenType fonts and Unicode, ensuring that unique linguistic characters render perfectly.
- **Modular Architecture (`\include`):** The dictionary will be split into hundreds of small `.tex` files organized by word root. This allows for rapid recompilation of specific sections and prevents Git merge conflicts during collaborative drafting.

### 3. Build & Version Management

- **Git:** Every generated root file and the master configuration is tracked in source control. This provides a clear history of changes and allows the curriculum team to "roll back" to previous versions of specific entries if needed.
- **Build Script:** An automated build script `scripts/build_tex.sh` handles the generation and optional compilation using XeLaTeX.

---

### Workflow Overview

1. **Generate:** Run `./scripts/build_tex.sh`.
2. **Extract:** A Python script `scripts/generate_tex_dict.py` reads the `hierarchical-dict.json` and `underlying_stems.csv`.
3. **Structure:** Individual `.tex` snippet files are created for each root in `artifacts/tex/roots/`.
4. **Stitch:** A master `main.tex` file pulls these snippets together.
5. **Compile:** If `xelatex` is available, it produces a high-quality, print-ready PDF at `artifacts/tex/main.pdf`.

---

**Font Requirements:**

- The current template uses **Plantagenet Cherokee**, which is standard on macOS and provides excellent support for both Latin and Cherokee characters.
