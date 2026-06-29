---
id: TASK-15.5
title: Refactor pronominal derivation to morphology
status: Done
assignee: []
created_date: '2026-06-29 18:04'
updated_date: '2026-06-29 18:16'
labels: []
dependencies: []
parent_task_id: TASK-15
ordinal: 43000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Refactor pronominal and prepronominal stripping logic from dictionary_pipeline.phases.identify_prefixes into a shared morphology utility 'derive_pronouns(examples: list[tuple[str, WordSpec]])' so it can be reused by both verb and noun pipelines.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Run pre-refactor tests and verify they pass
- [x] #2 Move pronominal/prepronominal derivation logic into morphology as a shared derive_pronouns function
- [x] #3 Verify all existing tests pass after refactoring
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Refactored pronominal prefix stripping logic into shared morphology/derivation.py, verified all 83 unit/integration tests pass, and ran the main dictionary pipeline confirming identical coverage/unique root selection on the main corpus.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Successfully refactored pronominal prefix stripping logic into morphology/derivation.py with generalized heuristics, integrated it into the verb pipeline, and verified correctness with no regression on the main verb corpus.
<!-- SECTION:FINAL_SUMMARY:END -->
