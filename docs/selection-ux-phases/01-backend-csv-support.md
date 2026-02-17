# Task 1: Backend CSV Support

## Description

Update the backend to support the new `pipeline_selected` column in `artifacts/corpora/validated_reconstructable_roots.csv` and implement the logic to pre-populate it.

## Steps

1.  **Modify `king_recreation/phases/reconstruct_and_validate/artifacts.py`**:
    - Update `save_validated_roots` to include `pipeline_selected` in the `fieldnames` list.
2.  **Modify `king_recreation/phases/select_canonical_derivations/__init__.py`**:
    - Update `select_canonical_derivations` logic.
    - When iterating through derivations, identify the "canonical" choice (the one with the shortest `h_grade_root` as per existing `dedupe_roots` logic).
    - Mark this choice by setting `pipeline_selected = 'x'` for that specific row.
    - Ensure the updated data is saved back to `artifacts/corpora/validated_reconstructable_roots.csv`.
3.  **Verification**:
    - Run `python -m king_recreation.phases.select_canonical_derivations` (or the full pipeline).
    - Check the CSV to ensure the new column exists and is populated correctly.
