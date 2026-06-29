---
id: TASK-19
title: TASK-15.5 - Refactor pronominal and prepronominal stripping logic
status: Done
assignee:
  - '@myself'
created_date: '2026-06-29 18:11'
updated_date: '2026-06-29 18:13'
labels: []
dependencies: []
ordinal: 43000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Refactor pronominal and prepronominal stripping logic into morphology/derivation.py or integrated into reconstruction.py using generalized heuristics.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Replace Prediction/form_name logic with WordSpec checks in prepronominal stripping
- [x] #2 Implement pronominal loops heuristics using person, number, aspect
- [x] #3 Integrate derive_pronouns in verb pipeline prefix identification
- [x] #4 Integrate derive_pronouns in noun pipeline runner and tests where needed
- [x] #5 All tests pass
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Refactored pronominal and prepronominal prefix stripping logic into derive_pronouns in morphology/derivation.py. Generalised heuristics based on WordSpec attributes rather than form names and Predictions. Integrated derive_pronouns into verb pipeline prefix identification. All tests pass successfully.
<!-- SECTION:FINAL_SUMMARY:END -->
