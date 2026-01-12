# General /h/ Alternation Plan

## Problem

The current /h/ alternation logic is brittle because it relies on the /h/ being at specific positions (start of stem or after initial vowel). The user indicates that the alternated (dropped) /h/ can be **anywhere** in the stem (e.g., `ahkwiyv` -> `akwiyv`, or hypothetically `galhqi` -> `galqi`).

Simply trying to "restore" /h/ by guessing its position during derivation leads to a combinatorial explosion and ambiguity.

## Proposed Solution

### 1. Unified "Drop First /h/" Rule

We assume the phonological rule is: **In h-dropping pronominal contexts (e.g., 2nd-to-3rd, 1st Set A), the _first_ /h/ in the stem is dropped, regardless of its position.**

### 2. Derivation Logic Update (`derive_stems.py`)

Instead of trying to _guess_ and generate restored stems (like `hstem`, `vHstem`) for every form independent of others, we should switch to a **Consensus Stem** approach.

- **Step A: Generate Literal Stems**: For all forms, strip prefixes and store the literal reaminder. Mark forms that are from "h-dropping" sets.
- **Step B:Identify Candidate Consensus Stems**: Use the stems derived from **non-h-dropping** forms (e.g., Present 3rd Set A, Imperfective) as the "Target Stems" (since they preserve the full underlying form).
- **Step C: Validate Targets**: For each "Target Stem", check if it explains the "h-dropping" forms.
  - A Target Stem `T` explains a dropping form `D` if:
    - `T == D` (The h wasn't dropped, or wasn't there to begin with)
    - OR `drop_first_h(T) == D` (The h was correctly dropped according to the rule)
- **Step D: Select**: If a Target Stem explains all forms, select it as the Present Stem.

This eliminates the need to guess where to insert /h/ in the dropping forms; we simply verify if the preserved form matches the dropped form via the rule.

### 3. Reconstruction Logic Update (`reconstruct_from_roots.py`)

Update `generate_pronominal_forms` to apply the generalized rule:

- If in an h-dropping set:
  - Find the index of the first `h` in the stem.
  - If found, generate a candidate form with that `h` removed.
  - (Optionally preserve the non-dropped form if the rule is variable/optional, but usually it's obligatory in these contexts).

## Implementation Steps

1.  **Modify `phonology_data.py`** (Optional): Ensure h-dropping sets are clearly identified.
2.  **Refactor `derive_stems.py`**:
    - Remove the ad-hoc `h + remainder` and `v + h + remainder` restoration logic in `test_config`.
    - Implement the `drop_first_h(stem)` helper function.
    - Rewrite the selection logic to use the "Consensus Stem" validation described above.
3.  **Update `reconstruct_from_roots.py`**:
    - Replace specific `startswith('h')` checks with a general `stem.find('h')` check to identify the char to drop.
4.  **Verify**:
    - Test with `ahkwiyv` (h at index 1).
    - Test with `hlogi` (h at index 0).
    - Test with deep h cases if available in corpus.

## Advantages

- **Robust**: Handles `h` at index 0, 1, 10, etc.
- **Efficient**: No blind generation of candidates.
- **Consistent**: Uses the "strong" forms to disambiguate the "weak" forms.
