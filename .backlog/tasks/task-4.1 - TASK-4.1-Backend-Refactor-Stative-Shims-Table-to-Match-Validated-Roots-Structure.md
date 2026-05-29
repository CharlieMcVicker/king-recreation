---
id: TASK-4.1
title: >-
  TASK-4.1 - Backend: Refactor Stative Shims Table to Match Validated Roots
  Structure
status: Done
assignee:
  - antigravity
created_date: '2026-05-29 14:07'
updated_date: '2026-05-29 15:04'
labels: []
dependencies: []
documentation:
  - dictionary_pipeline/row_models.py
  - dictionary_pipeline/phases/select_canonical_derivations/__init__.py
modified_files:
  - curated/stative_shims.csv
  - dictionary_pipeline/row_models.py
  - dictionary_pipeline/phases/select_canonical_derivations/__init__.py
  - root-based-dict/src/lib/data.ts
parent_task_id: TASK-4
priority: medium
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Align the structure of curated/stative_shims.csv with curated/validated_reconstructable_roots.csv so that all candidate forms are listed, the pipeline selection is marked, and user selection can be curated in its own column. Update the Python models (RowModelBase, DictionaryVerb/Morphology serialization) and loaders to read and write using this new format.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 curated/stative_shims.csv contains the same columns as curated/validated_reconstructable_roots.csv (including user_selected, pipeline_selected, prediction, class, etc.).
- [ ] #2 The loading logic (load_stative_shims) reads all rows and supports user_selected/pipeline_selected markings.
- [ ] #3 All existing shims are migrated to the new CSV format without data loss.
- [ ] #4 Pipeline tests verify that the shims data is read and written in the new structure.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Move ValidatedRootRow from reconstruct_and_validate/artifacts.py to row_models.py.
2. Update load_stative_shims() in select_canonical_derivations/__init__.py to read the multi-row candidate structure grouped by corpus_id.
3. Implement save_stative_shims() or inline writing inside select_canonical_derivations() to write all shim candidates back to stative_shims.csv, retaining user curation.
4. Write a Python migration script to migrate current curated/stative_shims.csv entries to the new structure matching validated_reconstructable_roots.csv.
5. Update root-based-dict/src/lib/data.ts (StativeShimRow, getStativeShims, updateStativeShim) and page.tsx to support the new structure.
6. Verify and run pytest to ensure tests pass.
<!-- SECTION:PLAN:END -->
