# Stem Derivation Specification

## Overview

This document specifies the algorithm and rules for deriving King's Verb Classes and stems from raw CED corpus data. The process involves identifying pronominal and pre-pronominal prefixes, handling phonological alternations (like h-dropping and metathesis), and extracting consistent stems across 5-6 verb forms.

## Core Goal

For each verb entry (row) in the corpus:
1.  **Identify the Configuration**: Determine the correct combination of:
    *   Set A / Set B inflection.
    *   Imperative target (2nd->3rd vs normal).
    *   Pre-pronominal prefixes (Translocutive, Partitive, Distributive).
2.  **Extract Stems**: Isolate the verb stem from each of the 5-6 provided forms (Present, 1sg, Imperfective, Perfective, Imperative, Infinitive).
3.  **Validate Consistency**: Ensure the extracted stems are phonologically compatible with a single underlying root/stem.

## Algorithm: Consensus Stem Derivation

Instead of guessing stems from individual forms in isolation, we use a **Consensus Approach**:

1.  **Generate Literal Stems**: For every form, generate all possible "literal" stems by stripping valid prefix combinations.
2.  **Identify Candidates**: Collect a set of "Candidate Stems" from the forms that are **phonologically stable** (i.e., not subject to h-dropping rules). These are typically the *Present*, *Imperfective*, and *Perfective* forms.
3.  **Validate**: For each Candidate Stem, check if it can "explain" every other form's observed literal stem.
    *   **Strict Check (Present/1sg)**: The observed stem must match the Candidate Stem exactly, or share a significant prefix (length >= 3).
    *   **Loose Check (Others)**: The observed stem must share the same starting character as the Candidate Stem.
    *   **H-Dropping**: If the form is in an h-dropping context (e.g., 1st Set A, 2nd->3rd), the observed stem can match the `drop_first_h(Candidate)` version.
    *   **Vowel Restoration**: If h-dropping removes a consonant cluster that blocked a vowel, the observed stem might show a restored vowel (e.g., `akhth...` -> `akath...`). This is checked via `is_compatible_with_vowel_restoration`.
4.  **Select Best Match**: If multiple valid derivations exist, prioritize the one where the derived stems have the highest character overlap with the Candidate Stem.

## Phonological Rules

### 1. Pronominal Prefixes (Sets A & B)

*   **Set A**: Used for Present, Imperfective (3rd person).
*   **Set B**: Used for Perfective, Infinitive (3rd person).
*   **Imperative**: Uses 2nd Person (Set A or B depending on verb class, or specialized 2nd->3rd prefixes).
*   **1st Person**: 1st Set A or B, or 1st->3rd.

Specific prefix shapes (e.g., `k-`, `a-`, `u-`, `ts-`) depend on the **Stem Initial** sound (Vowel vs Consonant, specific vowels, etc.). See `phonology_data.py` for the complete mapping.

### 2. Pre-Pronominal Prefixes

*   **Translocutive**: `w-` (vowels), `wi-` (consonants), `hw-` (before h).
*   **Partitive**: `n-` (vowels), `ni-` (consonants), `hn-` (before h).
*   **Distributive**: `t-`/`te-`/`ts-` variations.

### 3. H-Alternation (Generalized)

*   **Rule**: In specific contexts (1st Set A, 1st->3rd, 2nd->3rd), the **first /h/ in the stem** is dropped.
    *   Example: `ahkwiyv` -> `akwiyv`
    *   Example: `hlogi` -> `logi`
*   **Vowel Restoration**: Sometimes dropping /h/ breaks a cluster and allows an underlying vowel to surface.
    *   Example: `akhthastih` (3rd) -> `akathastih` (1st, h-dropped).

### 4. Split Stems (1st Person Irregularity)

The 1st Person Singular form is allowed to have a "split stem" that differs from the consensus stem derived from the 3rd person forms. This accommodates irregular verbs (e.g., "changing clothes") where the 1st person stem morphology diverges significantly but is still valid.

## Artifacts

*   **Output**: `artifacts/data/stem_corpus.csv` (Successfully parsed verbs).
*   **Failures**: `artifacts/reports/stem_derivation_failures.csv` (Verbs that could not be parsed).
*   **Debug Tool**: `king_recreation/analyze_failure.py` can be used to trace the derivation logic for any specific verb.