---
id: TASK-14
title: >-
  Implement Stative-no-imp and Eventful-imp-inf prediction enums and schema
  support
status: Done
assignee: []
created_date: '2026-06-22 15:46'
updated_date: '2026-06-22 16:48'
labels: []
dependencies: []
priority: medium
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Introduce a new kind of stative/shim pair: Stative-no-imp (which is like stative but has no imperative entry) and Eventful-imp-inf (which will have only imperative and infinitive forms).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Prediction enum in dictionary_forms.py includes STATIVE_NO_IMP and IMP_INF_EVENTFUL
- [x] #2 ROW_PREDICTION_SPECS maps and parses StativeNoImp rows
- [x] #3 Aspect mapping and Form names are defined for the new prediction enums
- [x] #4 The pipeline's canonical derivation and shim selection logic correctly matches IMP_INF_EVENTFUL shims to STATIVE_NO_IMP base verbs
- [x] #5 Unit tests verify the new enums, aspect mapping, and selection/compatibility logic
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented STATIVE_NO_IMP and IMP_INF_EVENTFUL prediction enums, mapped their aspects, updated selection and shim-binding logic in canonical selection, and wrote passing unit tests.
<!-- SECTION:FINAL_SUMMARY:END -->
