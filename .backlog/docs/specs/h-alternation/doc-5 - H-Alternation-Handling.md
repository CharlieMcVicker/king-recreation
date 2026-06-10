---
id: doc-5
title: H-Alternation Handling
type: specification
created_date: '2026-06-10 16:17'
---# H-Alternation Handling

This document details how `/h/` alternation is handled across various phases of the King Recreation pipeline. Instead of programmatically re-inserting `/h/`s, the system uses a **Dual Grade** root strategy, relying on both 3rd person and 1st person forms to determine stem behavior.

---

## 1. Implementation Phases

### A. Preprocessing
H-alternation handling begins in the preprocessing phase in [preprocess_ced/__init__.py](../../../../dictionary_pipeline/phases/preprocess_ced/__init__.py), specifically via the [respell_consonants](../../../../dictionary_pipeline/phases/preprocess_ced/__init__.py#L70) function:
- **Respelled Resonants**: Sequences of `h` followed by a resonant (`hn`, `hl`, `hy`, `hw`) are normalized to follow the resonant (`nh`, `lh`, `yh`, `wh`) to simplify stem comparisons.
- **Surface Aspiration**: Heuristics are applied to mark surface aspiration (e.g., `sl` -> `slh`).

### B. Stem Derivation & Prefix Identification
During prefix and stem identification in [morphology/morphemes/prefixes/](../../../../morphology/morphemes/prefixes/), the engine extracts stems from stripped forms and verifies their consistency across grades:
- **Candidate Selection**: An `h-candidate` is derived from the `present` form, and a `g-candidate` (glottal grade) is derived from the `present_1sg` form.
- **Consistency Check**: Verifies that:
  - All forms intended for a specific grade (h or glottal) are strictly compatible with their respective candidates.
  - The `h-candidate` and `g-candidate` are compatible.

### C. Root Extraction
The final validated roots are stored in the curated file [validated_reconstructable_roots.csv](../../../../curated/validated_reconstructable_roots.csv):
- **h-grade root**: The consensus stem derived primarily from the `present` form.
- **glottal-grade root**: The consensus stem derived from the `present_1sg` form.

### D. Reconstruction
The [ReconstructionEngine](../../../../morphology/reconstruction.py#L65) uses the dual roots to generate forms:
- **Grade Selection**: The engine calls `use_glottal_grade` to decide which root to use.
- **Pronominal Config**: Selection depends on the `PronominalConfig` (e.g., Set A vs Set B, or presence of 3rd person objects).

---

## 2. Grade Assignment & Logic

### Root Grades
1. **h-grade**: The unalternated stem, used by most forms.
2. **glottal-grade**: The `/h/` alternated stem (often containing a glottal stop `'`), used when specific pronominal triggers are met.

### Grade Selection Table
The grade used for reconstruction is determined by the pronominal configurations:

| Pronominal Set | Grade |
| :--- | :--- |
| `3rd Set A` / `3rd Set B` | **h-grade** |
| `2nd Set A` / `2nd Set B` | **h-grade** |
| `1st Set B` | **h-grade** |
| `1st Set A` | **glottal-grade** |
| `1st to 3rd` (transitive) | **glottal-grade** |
| `2nd to 3rd` (transitive) | **glottal-grade** |

> [!NOTE]
> `present_1sg` uses **glottal-grade** if the verb uses Set A prefixes or is transitive (1st to 3rd), otherwise it uses **h-grade** (Set B).

### Compatibility Mechanics
Compatibility between grades is verified in [morphology/h_alternation.py](../../../../morphology/h_alternation.py) using [possible_alternates](../../../../morphology/h_alternation.py) (which checks: direct match, H-dropping, H-to-glottal transitions, deaffricated lateral transitions like `lh` -> `tl`, and vowel restoration).
