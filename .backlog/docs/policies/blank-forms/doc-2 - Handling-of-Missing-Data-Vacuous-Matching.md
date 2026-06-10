---
id: doc-2
title: Handling of Missing Data (Vacuous Matching)
type: specification
created_date: '2026-06-10 16:10'
---

This document establishes the project-level policy for handling missing data (blank forms) in the verb corpus.

## Core Principle: Vacuous Matching

Missing data (blank forms) should be treated as **vacuously matching** any pattern or theory being tested.

- **Definition**: If a data point is missing (e.g., an empty string for the Infinitive form), it cannot contradict any hypothesis about what that form _should_ be. Therefore, it is consistent with _all_ hypotheses.
- **Interpretation**: A verb with missing forms is not "broken"; it is simply less constrained. It should be treated as a potential member of any class that is consistent with its _existing, non-blank_ forms.

## Pipeline Implementation

### 1. Preprocessing

- **Current State**: Converts varying "no data" markers to empty strings in [preprocess_ced/__init__.py](file:///Users/charlesmcvicker/code/king-recreation/dictionary_pipeline/phases/preprocess_ced/__init__.py).
- **Policy Implication**: **No Change**. Maintain consistent normalization of missing data to empty strings (`""`).

### 2. Verb Classification (Matching)

- **Goal**: Determine which conjugation classes a verb fits into.
- **Policy Implication**:
  - When checking if a verb matches a Class Pattern (e.g., _Class A_ requires suffix `-a` in the Imperative) via [class_patterns.py:L116](file:///Users/charlesmcvicker/code/king-recreation/morphology/morphemes/aspect/class_patterns.py#L116):
    - If the verb has a string for the Imperative, it must match `-a`.
    - If the verb has a **blank** for the Imperative, it is considered a **MATCH** for `-a` (and `-i`, and `-u`, etc.).
  - **Result**: Verbs with missing forms will likely match _more_ classes than fully specified verbs. A verb with 4 missing forms will match every class that is compatible with its 1 known form.

### 3. Stem Derivation

- **Goal**: Extract the underlying root/stem from the surface forms.
- **Policy Implication**:
  - **Do not drop verbs** simply because they have < 5 forms.
  - Attempt derivation on the forms that _are_ present.
  - **Consistency Checks**: If a derivation rule requires comparing Form X and Form Y (e.g., checking Set A vs Set B consistency), and one is missing:
    - Assume consistency (pass the check).
  - **Stem Availability**: If the specific form required to _source_ a stem is missing (e.g., using Present form to find Present Stem), that specific stem cannot be derived. However, derivation should proceed for other stems/roots if their source forms exist.

### 4. Analysis & Reporting

- **Goal**: Calculate coverage statistics and classify verbs.
- **Policy Implication**:
  - **Inclusion**: Verbs with blank forms are no longer "unmatched errors". They are valid data points.
  - **Matches**: Count them as matches for every class they vacuously fit.
  - **Nuance**: In reporting, it may be beneficial to distinguish between "Strict Full Matches" (all forms present and matching) and "Compatible Matches" (forms present match, others are blank). However, the top-level metric should accept vacuous matches.

### 5. Reconstruction & Validation

- **Goal**: Generate theoretical forms from a root and verify they match the corpus.
- **Policy Implication**:
  - **Reconstruction**: Generate _all_ forms for the paradigm, effectively "filling in the blanks" with the predicted theoretical forms.
  - **Validation (The "No Contradiction" Test)**:
    - Compare `Generated Form` vs `Corpus Form`.
    - If `Corpus Form` is `""` (blank): **PASS**. The theory predicts a value, and the corpus does not contradict it.
    - If `Corpus Form` is `"string"`: Must match exactly.
