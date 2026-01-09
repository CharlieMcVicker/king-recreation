# Reconstruction from Roots Specification

This document outlines the system for reconstructing full verb forms from a single root and metadata, and validating them against the original corpus.

## Core Logic

### 1. Classification & Root Extraction

The process begins by analyzing the `stem_corpus.csv` to identify verbs that can be reconstructed.

**Logic:**

1.  **Input**: Iterate through each verb in the stem corpus.
2.  **Match**: Apply classification logic to the _stem forms_ (present, imperfective, perfective, imperative, infinitive) against `king_classes.csv`.
3.  **Strict Full Match Criteria**:
    - All 5 forms must strictly match the class endings.
    - The remaining stem (after stripping ending) must be consistent across all forms (this is the **Root**).
    - _Note:_ `stem_corpus.csv` forms are stems (prefixes removed). Matching against class endings (suffixes) yields the naked Root.

**Data Model**:
A "Reconstructible Verb" consists of:

- Definition
- Root
- Class ID
- Metadata: `set_a_b`, `2_to_3`, `translocutive` (T), `partitive` (P), `distributive` (D).

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

### 3. Validation

**Input**: Generated forms and `artifacts/corpus.csv` (Reference).

**Logic**:

- For each verb, check if the Reference form (from `corpus.csv`) is present in the set of Generated forms.
- If the reference form matches any of the generated variants, the reconstruction is considered successful.

## Ambiguity Resolution

1.  **Prefix Variants**: The generator produces **all valid prefix variants** for a given condition (e.g., both `a-` and `ka-`).
2.  **Consistency Constraint**: The _same_ variant must be used across all forms of a specific verb if the condition applies to multiple forms. Verification checks consistency at the outer level.
