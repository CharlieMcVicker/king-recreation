---
id: TASK-17
title: Refactor WordSpec and Prefix rules to use SyntacticCategory
status: Done
assignee:
  - '@agent-17'
created_date: '2026-06-29 17:53'
updated_date: '2026-06-29 17:54'
labels: []
dependencies: []
ordinal: 41000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Introduce a unified SyntacticCategory enum to clean up noun/verb distinctions in prefix application rules.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Ensure pre-tests run and add tests for category-based prefix rules
- [x] #2 Refactor WordSpec, prepronominals.py, and dictionary_forms.py to use SyntacticCategory
- [x] #3 Verify all tests pass post-refactoring
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Ran pre-tests. Introduced SyntacticCategory enum in morphology/word_spec.py and added syntactic_category field to WordSpec. Refactored prepronominals.py to use spec.syntactic_category instead of checking aspects directly. Updated FormSpec, get_form_spec, and _build_wordspec in dictionary_forms.py. Added new test verifying syntactic_category logic.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Refactored the aspect-based prefix rules in prepronominals.py to leverage the new SyntacticCategory enum, simplifying prefix rules and decoupling them from aspects directly. All existing and new tests pass.
<!-- SECTION:FINAL_SUMMARY:END -->
