---
id: TASK-21.1
title: 'Phase 2: Generate Noun Hypotheses'
status: Done
assignee:
  - '@agent'
created_date: '2026-06-29 22:18'
updated_date: '2026-06-29 22:54'
labels: []
dependencies: []
parent_task_id: TASK-21
ordinal: 46000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Iterate over the noun corpus and generate WordSpec template hypotheses by stripping pronominals and nominalizing suffixes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Define NounHypothesis dataclass holding original word, WordSpec, and stem
- [x] #2 Strip known nominalizing suffixes per NounStructure rules (e.g. i, v'i, o'i)
- [x] #3 Generate multiple hypotheses when a noun matches multiple structural rules
- [x] #4 Attempt to strip third-person prefixes (u-, a-, u-ni-, a-ni-) during hypothesis generation
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented generate_hypotheses.py that uses morphology to strip nominalizing suffixes and 3rd person pronominals, generating WordSpecs. Covered by unit tests and integrated into __main__.py
<!-- SECTION:FINAL_SUMMARY:END -->

## Definition of Done
<!-- DOD:BEGIN -->
- [x] #1 Unit tests pass for hypothesis generation
<!-- DOD:END -->
