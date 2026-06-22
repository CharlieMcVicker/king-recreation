---
id: TASK-14.2
title: Update canonical derivation and shim selection logic for new enums
status: Done
assignee:
  - '@myself'
created_date: '2026-06-22 15:52'
updated_date: '2026-06-22 16:47'
labels: []
dependencies: []
parent_task_id: TASK-14
priority: medium
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Modify select_canonical_derivations/__init__.py to allow matching IMP_INF_EVENTFUL shims to STATIVE_NO_IMP base verbs. Ensure compatibility checking, curated overrides matching, and serialization handle the new pair correctly.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 select_canonical_derivations resolves and binds IMP_INF_EVENTFUL shims to STATIVE_NO_IMP base verbs
- [x] #2 stative_shims.csv correctly saves candidates of type IMP_INF_EVENTFUL
- [x] #3 Deduplication and serialization process STATIVE_NO_IMP and IMP_INF_EVENTFUL correctly
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Modify select_canonical_derivations/__init__.py to include STATIVE_NO_IMP and IMP_INF_EVENTFUL in the root deduplication, selection, and stative shims grouping/saving.\n2. Run the dictionary pipeline to regenerate shims and validated roots.\n3. Run tests to verify compatibility and correctness of the mappings, particularly for corpus_id 1564 and 521.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Updated select_canonical_derivations to correctly group, deduplicate, serialize, and save shims of prediction type IMP_INF_EVENTFUL and base verbs of prediction type STATIVE_NO_IMP.
<!-- SECTION:FINAL_SUMMARY:END -->
