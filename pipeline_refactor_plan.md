# Pipeline Refactor Status: COMPLETED

All planned changes to the stem derivation and classification pipeline have been implemented and verified.

## Completed Changes

1.  **Dependency Switch**: `classify_verbs.py` now strictly consumes `artifacts/data/stem_corpus.csv`.
2.  **Shared Logic**: Created `king_recreation/stem_analysis.py` as a Single Source of Truth for root extraction and consistency checking.
3.  **New Match Scope**: Added the **`reconstructs`** scope to the matching and analysis layers.
4.  **Integrated Reconstruction**: `reconstruct_from_roots.py` now relies on the `reconstructs` scope from the classification output.
5.  **Analytics Integration**: `analyze_matches.py` and `visualize_analysis.py` fully support reporting on the `reconstructs` metric.

## Outstanding Work (Frontend)

The following UI updates are still outstanding but were marked as out of scope for the core pipeline implementation:

### Frontend

- `MatchExplorer.tsx`:
  - Add `reconstructs` to the `scopeFilter` dropdown.
  - Add a visual indicator (e.g., a new color like Purple or Blue) for `reconstructs` scope.
  - Add a row or indicator in the "Match Details" view for "Root Consistency".
