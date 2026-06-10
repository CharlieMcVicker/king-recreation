---
id: doc-13
title: Consensus H-Alternation Plan
type: specification
created_date: '2026-06-10 16:30'
---

# Consensus /h/ Alternation Plan

This document outlines the consensus-based approach for handling /h/ alternation (dropping) in the stem during morphology derivation.

## Problem

The original /h/ alternation logic was brittle because it relied on the /h/ being at specific positions (start of stem or after initial vowel). However, the alternated (dropped) /h/ can be **anywhere** in the stem (e.g., `ahkwiyv` -> `akwiyv`, or `galhqi` -> `galqi`).

Simply trying to "restore" /h/ by guessing its position during derivation leads to a combinatorial explosion and ambiguity.

## Solution: Consensus Stem Approach

### 1. Unified "Drop First /h/" Rule

We assume the phonological rule is: **In h-dropping pronominal contexts (e.g., 2nd-to-3rd, 1st Set A), the _first_ /h/ in the stem is dropped, regardless of its position.**

### 2. Derivation Logic (`dictionary_pipeline/phases/identify_prefixes/`)

Instead of trying to guess and generate restored stems (like `hstem`, `vHstem`) for every form independent of others, we use a **Consensus Stem** approach:

- **Step A: Generate Literal Stems**: For all forms, strip prefixes and store the literal remainder. Mark forms that are from "h-dropping" sets.
- **Step B: Identify Candidate Consensus Stems**: Use the stems derived from **non-h-dropping** forms (e.g., Present 3rd Set A, Imperfective) as the "Target Stems" (since they preserve the full underlying form).
- **Step C: Validate Targets**: For each "Target Stem", check if it explains the "h-dropping" forms.
  - A Target Stem `T` explains a dropping form `D` if:
    - `T == D` (The h wasn't dropped, or wasn't there to begin with)
    - OR `drop_first_h(T) == D` (The h was correctly dropped according to the rule)
- **Step D: Select**: If a Target Stem explains all forms, select it as the Present Stem.

This eliminates the need to guess where to insert /h/ in the dropping forms; we simply verify if the preserved form matches the dropped form via the rule.

### 3. Reconstruction Logic (`morphology/h_alternation.py`)

Update `generate_pronominal_forms` to apply the generalized rule:
- If in an h-dropping set:
  - Find the index of the first `h` in the stem.
  - If found, generate a candidate form with that `h` removed.

## Advantages

- **Robust**: Handles `h` at index 0, 1, 10, etc.
- **Efficient**: No blind generation of candidates.
- **Consistent**: Uses the "strong" forms to disambiguate the "weak" forms.
