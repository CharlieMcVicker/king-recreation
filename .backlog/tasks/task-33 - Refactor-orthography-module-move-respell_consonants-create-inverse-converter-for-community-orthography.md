---
id: TASK-33
title: >-
  Refactor orthography module: move respell_consonants, create inverse converter
  for community orthography
status: Done
assignee:
  - '@agent-k'
created_date: '2026-08-12 13:49'
updated_date: '2026-08-12 13:52'
labels: []
dependencies: []
priority: high
ordinal: 59000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Refactor orthography module to house respell_consonants and its inverse function (convert_segment_to_community_orthography). Take plain string / list of segments instead of raw segmented string in conversion. Add unit tests verifying round-trip segment transformations.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Move respell_consonants into orthography module
- [x] #2 Implement inverse respell_consonants function for community orthography (accepting plain segment string/list)
- [x] #3 Update tex generators to map segments through community orthography before formatting
- [x] #4 Unit test segment conversion function
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Move respell_consonants from dictionary_pipeline/utils/text.py into dictionary_pipeline/orthography.py (and keep alias in text.py for backward compatibility).\n2. Create inverse function inverse_respell_consonants / convert_segment_to_community_orthography in orthography.py that accepts a plain segment string (e.g. 'kh' -> 'k', 'hs' -> 'sh', 'th' -> 't', 't' -> 'd', 'tsh' -> 'ch', etc., returning to g/k community orthography).\n3. Accept plain segment strings or a list of plain segment strings (not raw hyphenated strings with boundaries).\n4. Write pytest unit tests in tests/test_orthography.py verifying sample segments convert to community orthography.\n5. Update community_companion_generator.py to feed segment lists through this function before building formatted/colored LaTeX output.\n6. Verify all 101+ pytest unit tests pass.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Refactored orthography module: moved respell_consonants to orthography.py, implemented unrespell_consonants and convert_segment_to_community_orthography to accept plain segment strings/lists and convert to community orthography (g/k system). Added unit tests in test_orthography.py and verified 102/102 tests pass.
<!-- SECTION:FINAL_SUMMARY:END -->
