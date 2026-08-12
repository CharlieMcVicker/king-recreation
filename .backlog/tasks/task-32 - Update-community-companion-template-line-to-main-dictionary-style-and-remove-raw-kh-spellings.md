---
id: TASK-32
title: >-
  Update community companion template line to main dictionary style and remove
  raw kh spellings
status: Done
assignee:
  - '@agent-k'
created_date: '2026-08-12 13:43'
updated_date: '2026-08-12 13:48'
labels: []
dependencies: []
priority: high
ordinal: 58000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update template line in community companion 3-column view to match main dictionary template string format (using Set A (k-) for ka- verbs) and convert orthography in template lines so raw internal 'kh' does not appear.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Template line in 3-column minipage matches main dictionary template format
- [x] #2 Templates for ka- verbs show Set A (k-)
- [x] #3 No raw internal 'kh' appears in community companion template strings
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Inspect verb_config_to_tex function in tex_dictionary/generator.py to see how main dictionary templates are built (Set A (k-), parent classes, etc.).\n2. Refactor segment conversion to map segments through community orthography respelling (convert_to_community_orthography) BEFORE calling formatting functions so formatting logic is fully reusable.\n3. Identify candidate (input_segmented, expected_community_segmented) test pairs and propose them in the chat / write unit tests in tests/test_orthography.py.\n4. Update community_companion_generator.py to use verb_config_to_tex / community template formatting without raw 'kh' leaking.\n5. Run ./.venv/bin/pytest and ./.venv/bin/python -m tex_dictionary to verify.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Updated template lines in community companion 3-column view to match main dictionary format with Set A (ga) labels and full community orthography (no raw 'kh'). Refactored orthography conversion and passed all 101 pytest unit tests.
<!-- SECTION:FINAL_SUMMARY:END -->
