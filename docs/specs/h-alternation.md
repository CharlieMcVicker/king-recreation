# H-Alternation Handling

This document details how `/h/` alternation is handled across various phases of the King Recreation pipeline. Instead of programmatically re-inserting `/h/`s, the system uses a **Dual Grade** root strategy, relying on both 3rd person and 1st person forms to determine stem behavior.

## Implementation Phases

### 1. Preprocessing

H-alternation handling begins in `king_recreation/preprocess_ced.py` via the `respell_consonants` function.

- **Respelled Resonants**: Sequences of `h` followed by a resonant (`hn`, `hl`, `hy`, `hw`) are normalized to follow the resonant (`nh`, `lh`, `yh`, `wh`) to simplify stem comparisons.
- **Surface Aspiration**: Heuristics are applied to mark surface aspiration (e.g., `sl` -> `slh`).

### 2. Stem Derivation

In `king_recreation/derive_stems.py`, the `StemDeriver` extracts stems from stripped forms and verifies their consistency across grades.

- **Candidate Selection**: An `h-candidate` is derived from the `present` form, and a `g-candidate` (glottal grade) is derived from the `present_1sg` form.
- **Consistency Check**: `stems_are_consistent` ensures that:
  - All forms intended for a specific grade (h or glottal) are strictly compatible with their respective candidates.
  - The `h-candidate` and `g-candidate` are compatible via `phonology_data.grades_are_compatible`.

### 3. Root Extraction

The final roots are stored in `artifacts/data/derived_roots.csv`:

- **h-grade root**: The consensus stem derived primarily from the `present` form.
- **glottal-grade root**: The consensus stem derived from the `present_1sg` form.

### 4. Reconstruction

The `ReconstructionEngine` in `king_recreation/reconstruct_from_roots.py` uses the dual roots to generate forms.

- **Grade Selection**: The engine calls `use_glottal_grade(form, config)` to decide which root to use.
- **Pronominal Config**: Selection depends on the `PronominalConfig` (e.g., Set A vs Set B, or Presence of 3rd person objects).

## Grade Assignment & Logic

### Root Grades

1.  **h-grade**: The unalternated stem, used by most forms.
2.  **glottal-grade**: The `/h/` alternated stem (often containing a glottal stop `'`), used when specific pronominal triggers are met.

### Grade Selection Table

The grade used for reconstruction is determined by the `use_glottal_grade_for_set` function in `phonology_data.py`:

| Pronominal Set            | Grade             |
| :------------------------ | :---------------- |
| `3rd Set A` / `3rd Set B` | **h-grade**       |
| `2nd Set A` / `2nd Set B` | **h-grade**       |
| `1st Set B`               | **h-grade**       |
| `1st Set A`               | **glottal-grade** |
| `1st to 3rd` (transitive) | **glottal-grade** |
| `2nd to 3rd` (transitive) | **glottal-grade** |

> [!NOTE] > `present_1sg` uses **glottal-grade** if the verb uses Set A prefixes or is transitive (1st to 3rd), otherwise it uses **h-grade** (Set B).

### Compatibility Mechanics

Compatibility between grades is verified in `phonology_data.py` using `possible_alternates`, which checks:

1.  **Direct Match**: `h_grade == glottal_grade`
2.  **H-Dropping**: `_drop_first_h(h_grade) == glottal_grade`
3.  **H-to-Glottal**: `_first_h_to_glottal(h_grade) == glottal_grade`
4.  **Deaffricated Lateral**: `lh` -> `tl` transitions.
5.  **Vowel Restoration**: Syncopated vs restored vowel compatibility.
