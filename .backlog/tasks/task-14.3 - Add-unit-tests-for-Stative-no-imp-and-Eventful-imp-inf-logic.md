---
id: TASK-14.3
title: Add unit tests for Stative-no-imp and Eventful-imp-inf logic
status: Done
assignee:
  - '@myself'
created_date: '2026-06-22 15:52'
updated_date: '2026-06-22 16:47'
labels: []
dependencies: []
parent_task_id: TASK-14
priority: medium
ordinal: 33000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Write unit tests verifying the new enums, their aspect and form configurations, and their compatibility/shim-binding behavior within the selection pipeline.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Unit tests verify ROW_PREDICTION_SPECS parsing of StativeNoImp rows
- [x] #2 Unit tests verify validate_shim_compatibility with IMP_INF_EVENTFUL candidates
- [x] #3 Unit tests verify correct resolution and binding of IMP_INF_EVENTFUL shims in the pipeline
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Implement test_expected_shim_parses test function in tests/test_stative_shims.py allowing expected pairings of (corpus_id, stative_class, eventful_class) to be specified and checked for compatibility.\n2. Add the user's requested pairing ("521", "stative", "sk-h[imp2]") to test_expected_shim_parses.\n3. Add unit tests for ROW_PREDICTION_SPECS parsing of StativeNoImp rows.\n4. Run tests and verify.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Added unit tests verifying StativeNoImp row prediction specs parsing, shim compatibility for new enums, and expected shim parses for 1564. All tests pass.
<!-- SECTION:FINAL_SUMMARY:END -->
