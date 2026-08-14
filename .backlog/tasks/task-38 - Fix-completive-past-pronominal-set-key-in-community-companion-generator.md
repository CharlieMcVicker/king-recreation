---
id: TASK-38
title: Fix completive past pronominal set key in community companion generator
status: Done
assignee:
  - '@agent'
created_date: '2026-08-13 20:07'
updated_date: '2026-08-13 20:07'
labels: []
dependencies: []
ordinal: 64000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Fix form_name mapping in format_segmented_verb_community so completive form correctly passes 'perfective' to build_wordspec, allowing Set B pronominal colors to render blue instead of red.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Pass 'perfective' as form_name for completive aspect when calling format_segmented_verb_community in community_companion_generator.py
- [x] #2 Verify LaTeX output / generator runs cleanly
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Inspect companion_generator.py and community_companion_generator.py for any other occurrences of 'completive' passed as form_name to format_segmented_verb_community.\n2. Update community_companion_generator.py (and companion_generator.py if applicable) so format_segmented_verb_community resolves or receives 'perfective' as form_name for build_wordspec.\n3. Run tests / companion generator to verify correct execution.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Updated format_segmented_verb_community call in community_companion_generator.py to use 'perfective' instead of 'completive' for form_name. Verified that Set B verbs now render their completive past pronouns in RoyalBlue (e.g. \textcolor{RoyalBlue}{u}...) and all unit tests pass.
<!-- SECTION:FINAL_SUMMARY:END -->
