---
id: TASK-18
title: Create mapping function from NounStructure enum to WordSpec
status: Done
assignee:
  - '@myself'
created_date: '2026-06-29 17:57'
updated_date: '2026-06-29 17:57'
labels: []
dependencies: []
ordinal: 42000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Define a helper function to convert NounStructure enums to WordSpec objects and update unit tests to use it.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Define NounStructure enum and helper function in word_spec.py
- [x] #2 Update test_noun_morphology.py to test the helper function
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added get_noun_wordspec mapping helper function and verified with new tests.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented get_noun_wordspec mapping function from NounStructure enum to WordSpec, refactored existing tests to utilize it, and added a specific unit test to verify mapping properties.
<!-- SECTION:FINAL_SUMMARY:END -->
