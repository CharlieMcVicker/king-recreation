---
id: TASK-15
title: Extend WordSpec and Suffix Rules for nouns
status: In Progress
assignee:
  - '@subagent'
created_date: '2026-06-29 17:28'
updated_date: '2026-06-29 17:30'
labels: []
dependencies: []
modified_files:
  - morphology/morphology_types.py
  - morphology/word_spec.py
  - morphology/reconstruction.py
  - tests/test_noun_morphology.py
ordinal: 36000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Generalize WordSpec to support noun templates and define suffix rules for root, agentive, completive, and incompletive noun structures.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Generalize WordSpec to support noun templates
- [x] #2 Define suffix rules for root, agentive, completive, and incompletive noun structures
- [x] #3 Implement unit tests validating noun morphology suffix rules and template support
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Generalize WordSpec to support noun templates\n2. Define suffix rules for root, agentive, completive, and incompletive noun structures\n3. Add unit tests for noun morphology
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Generalized WordSpec to support noun templates (noun structures) and defined suffix rules for root, agentive, completive, and incompletive noun structures. Integrated these into the reconstruction engine, allowing bare and prefixed noun derivations. Added unit tests verifying suffix rules and reconstruction logic.
<!-- SECTION:FINAL_SUMMARY:END -->
