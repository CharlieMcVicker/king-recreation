# Reconstruction from Roots Implementation Plan

This document outlines the plan to create a script that reconstructs full verb forms from a single root and metadata, validating them against the original corpus.

## Goal

To verify that we can fully reconstruct verb forms in `corpus.csv` using:

1. A single **Root** (derived from `stem_corpus.csv` by stripping class endings).
2. **King Verb Class** (providing endings).
3. **Prefix Information** (Inflection Pattern/Set, Prepronominals, 2->3rd flag, derived in `stem_corpus.csv`).

## Steps

### 1. Script Creation

Create a new script `reconstruct_from_roots.py` (or integrated into `king_recreation` module) that performs the following:

### 2. Classification & Root Extraction

- **Input**: `artifacts/stem_corpus.csv`.
- **Logic**:
  - Iterate through each verb in the stem corpus.
  - Apply `classify_verbs` logic to the _stem forms_ (present, imperfective, perfective, imperative, infinitive) against `king_classes.csv`.
  - **Criteria**: Identify **Strict Full Matches**. A verb is a strict full match if:
    - All 5 forms strictly match the class endings.
    - The remaining stem (after stripping ending) is consistent (i.e., the "Root").
    - Note: `stem_corpus.csv` forms are stems (prefixes removed). Matching against class endings (suffixes) should yield the naked Root.
- **Output**: A list of "Reconstructible Verbs" containing:
  - Definition
  - Root
  - Class ID
  - Metadata: `set_a_b`, `2_to_3`, `translocutive` (T), `partitive` (P), `distributive` (D).

### 3. Reconstruction (Generation)

- **Input**: The "Reconstructible Verbs" list.
- **Logic**: Create a `Generator` class (inverse of `StemDeriver`?):
  - **Step 3a: Add Class Endings**
    - For each form (pres, imp, perf, imper, inf):
    - `Stem = Root + Class Suffix`
  - **Step 3b: Add Pronominal Prefix**
    - Determine abstract prefix category (e.g., "3rd Set A") based on `Set`, `Imp Type` (2->3), and `Form`.
    - Select specific prefix morph based on `Stem` phonology (vowel vs consonant).
    - **Ambiguity Handling**: If multiple prefixes are valid for a condition (e.g., `a-` vs `ka-` for consonants), generate _all_ valid variants.
  - **Step 3c: Add Prepronominal Prefixes**
    - Apply in order: `Distributive` -> `Partitive` -> `Translocutive` (Inner to Outer).
    - `Form = T(P(D(Pronoun(Stem))))`.
    - Handle phonological rules (e.g., `h` deletion/insertion, vowel coalescence) in reverse of the stripping logic.

### 4. Validation

- **Input**: Generated forms and `artifacts/corpus.csv` (Reference).
- **Logic**:
  - For each verb, check if the Reference form (from `corpus.csv`) is present in the set of Generated forms.
  - Log successes and failures.
- **Output**: `artifacts/reconstruction_report.csv` (or similar) summarizing the results.

## Decisions & Clarifications

1. **Ambiguity Resolution**:
   - The generator will produce **all valid prefix variants** for a given condition (e.g., trying both `a-` and `ka-` for 3rd Set A).
   - **Consistency Constraint**: The _same_ variant must be used across all forms of a specific verb if the condition applies to multiple forms. We will loop through valid variant sets at the outer level for each verb.
2. **Stem Corpus Reliability**:
   - We will use `stem_corpus.csv` as the source of truth for stems. We will not re-derive stems on the fly during this process.
3. **Phonological Reversibility**:
   - The script will identify and **flag potential lossy rules** (e.g., ambiguous vowel coalescences) where the reverse operation is not deterministic.
   - These flagged cases will be logged for user review, rather than attempting to guess or failing silently.

## Deliverables

- `reconstruct_from_roots.py` script.
- `artifacts/reconstruction_data.csv` (The "Spec" list).
- `artifacts/reconstruction_validation.json` (Validation results).
