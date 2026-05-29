---
id: TASK-4.2
title: >-
  TASK-4.2 - Backend: Implement Shim Configuration Matching and Pipeline
  Validation
status: To Do
assignee: []
created_date: '2026-05-29 14:07'
updated_date: '2026-05-29 14:13'
labels: []
dependencies:
  - TASK-4.4
documentation:
  - dictionary_pipeline/phases/select_canonical_derivations/__init__.py
modified_files:
  - dictionary_pipeline/phases/select_canonical_derivations/__init__.py
  - tests/test_feels_infeventful.py
parent_task_id: TASK-4
priority: medium
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement backend validation and join logic for stative shims. When reading curated/stative_shims.csv, validate that the selected shim matches the compatibility criteria defined in TASK-4.4. Crucially, suffix class and post-root morpheme (post_root_morpheme) MUST NOT be matched, as the shim's role is to explain the infinitive form using its own eventive class structure. Raise a hard error (exit(1)) if a user-selected shim choice cannot be joined during a pipeline run due to derivation/criteria changes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 If a curated shim cannot be joined (e.g., the base derivation changed so that the shim no longer matches the compatibility criteria scoped in TASK-4.4), the pipeline fails with an informative error.
- [ ] #2 Validation checks are run when reading curated/stative_shims.csv, verifying that candidates meet the compatibility criteria.
- [ ] #3 Unit tests are written to verify that invalid shims are rejected and that joining errors are correctly raised.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Refactor the shim loading and joining logic in `dictionary_pipeline/phases/select_canonical_derivations/__init__.py`.
2. Implement a validation function `validate_shim_compatibility(base_verb: DictionaryVerb, shim_candidate: DictionaryVerb) -> bool` using the matching criteria established in TASK-4.4.
3. Update the joining logic in `select_canonical_derivations()`:
   - Identify candidate InfEventful shims matching the base FullStative verb.
   - Run `validate_shim_compatibility()` on all candidates.
   - If there is a user-selected shim (marked with "x" in `user_selected` in `curated/stative_shims.csv`):
     - Assert it is still compatible with the base verb.
     - If it is incompatible (e.g. because the base verb's configuration changed), print a detailed error (explaining which fields mismatch) and terminate the process with `exit(1)`.
     - Otherwise, bind the chosen shim to the base verb (`canonical_verb.shim = chosen_shim`) and set `user_selected = "x"`.
   - If there is no user selection, sort the compatible candidates using `sort_candidates()` and bind the top choice, marking `pipeline_selected = "x"`.
   - Save the list of candidates with `user_selected` / `pipeline_selected` marks back to `curated/stative_shims.csv`.
4. Add new automated unit tests in `tests/` verifying that:
   - Compatible shims are correctly associated.
   - Incompatible shims fail validation.
   - The pipeline exits with error `exit(1)` when a previously saved user selection breaks compatibility.
<!-- SECTION:PLAN:END -->
