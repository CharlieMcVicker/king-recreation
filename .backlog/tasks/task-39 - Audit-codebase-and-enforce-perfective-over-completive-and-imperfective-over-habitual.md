---
id: TASK-39
title: >-
  Audit codebase and enforce 'perfective' over 'completive' and 'imperfective'
  over 'habitual'
status: Done
assignee:
  - '@agent'
created_date: '2026-08-13 20:08'
updated_date: '2026-08-13 20:08'
labels: []
dependencies: []
ordinal: 65000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Audit all references across codebase for 'completive' and 'habitual' form/aspect names in function calls, variables, and documentation, ensuring 'perfective' and 'imperfective' are consistently used.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Audit tex_dictionary module for 'completive' and 'habitual'
- [x] #2 Audit dictionary_pipeline module for 'completive' and 'habitual'
- [x] #3 Run test suite and verify TeX generation
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Search codebase for usages of 'completive' and 'habitual'.\n2. Replace occurrences where 'completive' or 'habitual' are passed as aspect/form identifiers with 'perfective' and 'imperfective'.\n3. Run pytest and TeX generator to confirm no regressions.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Audited tex_dictionary module for form_name parameters. Replaced 'habitual' with 'imperfective' (matching previous 'completive' -> 'perfective' update) so that form specs always use canonical aspect names across TeX generation. All 98 unit tests passed and TeX compilation succeeded cleanly.
<!-- SECTION:FINAL_SUMMARY:END -->
