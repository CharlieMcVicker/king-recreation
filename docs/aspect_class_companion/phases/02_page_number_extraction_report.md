# Phase 2: Accurate Page Number Extraction - Report

## Status: SUCCESS

## Completed Tasks
1. **Module Creation:**
   - Created `tex_dictionary/toc_parser.py`.
2. **Bracket-Aware Parser Implementation:**
   - Implemented `parse_main_toc(toc_path, known_class_names)`.
   - Uses a character-streaming approach (`_extract_balanced`) to correctly handle nested LaTeX macros and braces in `main.toc`.
   - Specifically handles nested square brackets (e.g., `[cause[perf2]]`) to accurately isolate the aspect class name.
3. **Data Extraction:**
   - Successfully extracts `verb_tex`, `definition`, and `page` number for each entry.
   - Cleans up trailing dashes and punctuation from `verb_tex`.
   - Returns a mapping of `aspect_class_name` -> `List[Dict]`.
4. **Path Configuration:**
   - Added `MAIN_TOC_PATH` to `king_recreation/paths.py`.

## Validation Results
- **TOC Coverage:** Successfully parsed `artifacts/tex/main.toc`.
- **Class Count:** Identified **55 distinct aspect classes** with associated verbs.
- **Specific Class Matches:**
  - `cause`: 85 verbs found.
  - `stative`: 20 verbs found.
  - `stative-h`: 17 verbs found.
  - `stative-k`: 7 verbs found.
  - `stative-s`: 4 verbs found.
  - `stative-a'`: 3 verbs found.
  - `stative-eh`: 2 verbs found.
- **Data Integrity:** Verified that `[cause[perf2]]` is correctly resolved to the `cause` class.
- **Sample Extraction:**
  - Verb: `\textcolor {Red}{Set A (k)}{-}\textbf {'n}{-}ihs`
  - Definition: `he/she is burying him/her`
  - Page: `19`

## Next Steps
Proceed to Phase 3: Mascot Variant Resolution. This will involve grouping the extracted verbs by their observed variant combinations and selecting the appropriate mascot for each variant.
