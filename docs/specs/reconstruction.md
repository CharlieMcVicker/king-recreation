# Reconstruction from Roots Specification

This document outlines the system for reconstructing full verb forms from a single root and metadata, and validating them against the original corpus.

## Core Logic

### 1. Classification & Root Extraction

The process begins by reading the `matches.csv` to identify verbs with the **`reconstructs`** scope.

**Logic:**

1.  **Input**: Iterate through verbs flagged as `reconstructs` in `matches.csv`.
2.  **Shared Interface**: Use `king_recreation/stem_analysis.py` to extract the root from the `stem_corpus.csv` data.
3.  **Validation Check**: The classification phase already performed the root consistency check; reconstruction consumes this result to ensure it works from a high-quality base.

- Definition
- Root
- Class ID
- Metadata:
  - `stem_type` (e.g. `con`, `vowel_a`)
  - `metathesis_strategy`
  - `set_a_b`
  - `use_ka_variant`, `use_uwa_for_3rd_set_b`, `use_aki_for_1st_set_b`
  - `use_3rd_person_object` (Implies 2->3 interaction)
  - `translocutive` (T), `partitive` (P), `distributive` (D).

### 2. Reconstruction (Generation)

The generator functions as the inverse of the stem derivation and classification process.

**Step 2a: Add Class Endings**
For each form (pres, imp, perf, imper, inf):
`Stem = Root + Class Suffix`

**Step 2b: Add Pronominal Prefix**

1.  Determine abstract prefix category (e.g., "3rd Set A") based on `Set`, `Imp Type` (2->3), and `Form`.
2.  Select specific prefix morph based on `Stem` phonology (vowel vs consonant).
    - **Ambiguity Handling**: If multiple prefixes are valid for a condition (e.g., `a-` vs `ka-` for consonants), generate _all_ valid variants.

**Step 2c: Add Prepronominal Prefixes**
Apply in order: `Distributive` -> `Partitive` -> `Translocutive` (Inner to Outer).
`Form = T(P(D(Pronoun(Stem))))`

_Phonological Rules:_ Handle `h` deletion/insertion and vowel coalescence in reverse of the stripping logic.

**Step 2d: H-Metathesis (If Applicable)**
If the verb is flagged as using metathesis in `stem_corpus.csv`, apply the metathesis variants:

- **Consonant**: `ka-` + `hnogi` -> `khanogi`, `tsha-` + `hnaskwalo` -> `tshanaskwalo`, `akhi-` + `hnaskwalo` -> `akhinaskwalo`
- **Vowel**: `k-` + `ehlatitoh` -> `khelatitoh`, `uw-` + `ehlatitoh` -> `uhwelatitoh`, `h-` + `ehlatita` -> `helatita`
- If the verb is _not_ flagged, these metathesized variants are skipped to avoid over-application.

### 3. Validation

**Input**: Generated forms and `artifacts/corpus.csv` (Reference).

**Logic**:

- For each verb, check if the Reference form (from `corpus.csv`) is present in the set of Generated forms.
- If the reference form matches any of the generated variants, the reconstruction is considered successful.

## Ambiguity Resolution

1.  **Prefix Variants**: The generator produces **all valid prefix variants** for a given condition (e.g., both `a-` and `ka-`).
2.  **Consistency Constraint**: The _same_ variant must be used across all forms of a specific verb if the condition applies to multiple forms. Verification checks consistency at the outer level.
