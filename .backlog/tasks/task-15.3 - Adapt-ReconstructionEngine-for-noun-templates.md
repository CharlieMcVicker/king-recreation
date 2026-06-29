---
id: TASK-15.3
title: Adapt ReconstructionEngine for noun templates
status: Done
assignee:
  - '@myself'
created_date: '2026-06-28 17:54'
updated_date: '2026-06-29 17:56'
labels: []
dependencies: []
parent_task_id: TASK-15
ordinal: 39000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update ReconstructionEngine to support noun template prefix/suffix parsing and verification.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Updated morphology/word_spec.py to remove old noun fields; simplified reconstruct_spec in morphology/reconstruction.py to reconstruct using spec.aspect directly; verified dictionary_pipeline/dictionary_forms.py maps noun structures to FormSpec and unified WordSpec properties; refactored tests/test_noun_morphology.py to construct WordSpec instances using aspect, syntactic_category, and tense_ending; all 81 unit tests pass successfully.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Successfully adapted the ReconstructionEngine for noun templates by removing the legacy noun_structure, noun_suffix, and noun_aspect properties from WordSpec, updating reconstruction logic to select stems using spec.aspect directly, and adapting the test cases to use the unified WordSpec properties syntactic_category, aspect, and tense_ending.
<!-- SECTION:FINAL_SUMMARY:END -->
