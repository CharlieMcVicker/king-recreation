# Phase 4: TeX Layout & Table Generation

## Goal
Generate the precise pedagogical tables and TOC-style cross-references for the companion document utilizing `pylatex`.

## Context
Visual clarity is paramount for second-language learners. We need 2-row tables highlighting both abstract endings and concrete mascot examples. Morphological segmentation (pronouns vs. aspect endings) must be clearly color-coded and bolded. Below the tables, we list all verbs in the class mapping exactly to their page numbers in the main dictionary.

## Step-by-Step Implementation
1. **Module Creation:**
   - Create `tex_dictionary/companion_generator.py`.
2. **Preamble & Setup:**
   - Initialize a `pylatex.Document`. Apply the exact identical preamble commands as `main.tex` (geometry, fonts like Noto Sans Cherokee, colors, title formatting).
3. **Aspect Class Sections:**
   - For each class (in frequency order determined from Phase 1):
     - Create a `\section*{Class: [ClassName]}`.
4. **Variant Table Construction:**
   - For each variant combination identified in Phase 3:
     - Instantiate a `Tabularx` table (columns: Class/Definition, Present, Imperfective, Perfective, Imperative, Infinitive).
     - **Row 1 (Endings):** Print the class variant name in Col 1. Fill Cols 2-6 with the raw aspect endings. (If it's a derived variant, only modified cells are populated).
     - **Row 2 (Mascot):** Print the Mascot's definition and its `main.toc` page number (if found) in Col 1. Fill Cols 2-6 with the Mascot's five reference forms.
     - **Formatting Logic:** Create a helper function `format_segmented_verb()` that processes the mascot form: wraps the Pronoun segment in LaTeX text colors (Red for Set A, Blue for Set B, Purple for P->P), and wraps the aspect ending segment in `\textbf{}`.
5. **Verb Cross-Reference Listing:**
   - Immediately beneath the table, generate a list (or `\paragraph` entries) similar to a TOC layout.
   - For every verb mathematically belonging to this class & variant, print its configured `verb_to_tex` string seamlessly followed by `\dotfill` (or similar) and its extracted page number from Phase 2.
6. **Validation:**
   - Review a sample `.tex` file output manually to ensure the `Tabularx` syntax and color-coding macros compile cleanly.
