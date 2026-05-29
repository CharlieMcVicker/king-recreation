---
id: TASK-4.1
title: >-
  TASK-4.1 - Backend: Refactor Stative Shims Table to Match Validated Roots
  Structure
status: To Do
assignee: []
created_date: '2026-05-29 14:07'
updated_date: '2026-05-29 14:13'
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
1. Refactor `stative_shims.csv` schema to match `validated_reconstructable_roots.csv`.
2. Update `dictionary_pipeline/row_models.py` to use a row model representing candidates in `stative_shims.csv` (e.g. reusing `ValidatedRootRow` or using an equivalent dataclass).
3. Update `load_stative_shims()` in `dictionary_pipeline/phases/select_canonical_derivations/__init__.py` to load all candidate rows from `curated/stative_shims.csv` into a structured list of candidates.
4. Write a Python migration script (or temporary setup code) to convert the existing single-row chosen shims in `stative_shims.csv` into the new multi-row format. Match each existing chosen shim back to the candidates for the corresponding stative verb, marking it as `user_selected = "x"`.
<!-- SECTION:PLAN:END -->
