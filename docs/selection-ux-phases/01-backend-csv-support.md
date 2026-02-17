# Task 1: Backend CSV Support (Completed)

## Description

Update the backend to support the new `pipeline_selected` column in `artifacts/corpora/validated_reconstructable_roots.csv` and implement the logic to pre-populate it.

## Implementation Details

### 1. Artifacts Update

- **File**: `king_recreation/phases/reconstruct_and_validate/artifacts.py`
- **Change**: Updated `save_validated_roots` to include `pipeline_selected` in the CSV header, positioned after `user_selected`.

### 2. Selection Logic Update

- **File**: `king_recreation/phases/select_canonical_derivations/__init__.py`
- **Logic**:
  - Iterate through all potential derivations for each corpus entry.
  - Identify the "canonical" choice based on the shortest `h_grade_root`.
  - Mark this choice by setting `pipeline_selected = 'x'` in the row data.
  - Save the updated data back to `artifacts/corpora/validated_reconstructable_roots.csv`.

### 3. Ambiguity Resolution & Stem Prioritization

- **Issue**: Previously, verbs with multiple derivations of the same shortest root length were dropped as "ambiguous". This caused ~200 verbs to be missing from the final reconstructable set.
- **Resolution**: Implemented deterministic tie-breaking.
  - **Primary Criteria**: Shortest `h_grade_root` length.
  - **Secondary Criteria (Stem Type Priority)**: `con` > `aspirated` > `s_stem` > others.
  - **Tie-Breaker**: Deterministic sort by `h_grade_root`, `class_name`, and original JSON data.
- **Recovered Verbs**: This change recovered 209 dropped verbs, ensuring all unique roots are represented.

## Verification

Run the pipeline phase:

```bash
python -m king_recreation.phases.select_canonical_derivations
```

Check `artifacts/corpora/validated_reconstructable_roots.csv` to confirm:

- The `pipeline_selected` column exists.
- Rows are marked with 'x' corresponding to the canonical derivation.
- No ambiguous dropped items are reported in the logs.
