---
id: TASK-11
title: Resolve Stative Shim validation compatibility issues
status: Done
assignee:
  - '@agent'
created_date: '2026-06-10 18:43'
updated_date: '2026-06-10 18:43'
labels: []
dependencies: []
modified_files:
  - dictionary_pipeline/phases/select_canonical_derivations/__init__.py
  - tests/test_stative_shims.py
priority: medium
ordinal: 27000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Debug and resolve why the compatible InfEventful shim for 'he/she is in prayer' (corpus ID 1450) was not showing up/included. Ensure load_stative_shims ignores user_selected and pipeline_selected columns when checking for curated overrides. Implement a unit test to verify compatibility.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Fix load_stative_shims to exclude curation selection columns from overrides dictionary
- [x] #2 Add a unit test verifying compatibility of FullStative and InfEventful predictions for 'he/she is in prayer'
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Modified load_stative_shims to strip user_selected and pipeline_selected columns from loaded overrides, ensuring they do not trigger validation mismatches. Created a pytest unit test verifying the compatibility of 'he/she is in prayer' (corpus ID 1450) and verified all tests pass.
<!-- SECTION:FINAL_SUMMARY:END -->
