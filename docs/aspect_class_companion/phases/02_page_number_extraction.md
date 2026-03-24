# Phase 2: Accurate Page Number Extraction

## Goal
Build a standalone, highly accurate parsing module to scrape verb definitions and their precise locations from the LaTeX-generated Table of Contents (`main.toc`).

## Context
Instead of deeply coupling our Python generator logic with LaTeX's internal page-breaking algorithms, we rely on the final `main.toc` emitted by `xelatex main.tex`. Since `main.toc` contains heavily nested LaTeX macros and brackets (e.g., `\textcolor{Red}{Set A (k)}`), simple regex is too brittle. We must use character-iteration to track depth.

## Step-by-Step Implementation
1. **Module Creation:**
   - Create `tex_dictionary/toc_parser.py`.
2. **Bracket Depth Tracking Algorithm:**
   - Implement a function `parse_main_toc(toc_path)` that opens `artifacts/tex/main.toc`.
   - Iterate character by character (or token by token) keeping a counter for `{` and `}`.
   - Identify lines beginning with `\contentsline {subsection}` or `\contentsline {subsubsection}`.
   - Extract the full content within the second major argument (the label string containing the verb's TeX, derivation tags, and definition).
   - Extract the content of the third major argument (the page number).
3. **Regex Extraction for Verb Classes:**
   - Once a label string is cleanly extracted from the `{}` blocks, use a targeted Regex to look for the aspect class tag safely encapsulated inside brackets, e.g., `\[hvsk-han\]` or `\[stative-h\]`. Note: A verb may have multiple tags (like `[cause][perf2]`); ensure the aspect class is accurately targeted.
4. **Return Data Structure:**
   - Return a dictionary mapping: `aspect_class_name` -> `List[Dict({'verb_tex': '...', 'page': '104'})]`.
5. **Validation:**
   - Write a unit test or validation script that asserts the parser successfully runs over the existing `artifacts/tex/main.toc` and accurately groups hundreds of verbs under the `[cause]` and `[stative]` keys without throwing bracket-mismatch errors.
