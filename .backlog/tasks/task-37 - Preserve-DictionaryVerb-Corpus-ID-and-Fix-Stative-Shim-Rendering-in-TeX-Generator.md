---
id: TASK-37
title: >-
  Preserve DictionaryVerb Corpus ID and Fix Stative Shim Rendering in TeX
  Generator
status: Done
assignee:
  - '@agent-k'
created_date: '2026-08-13 15:27'
updated_date: '2026-08-13 15:28'
labels: []
dependencies: []
ordinal: 63000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update community companion and main TeX generator modules to iterate through words using Corpus ID and exact DictionaryVerb objects, preventing incorrect active/stative template cross-over and fixing root key split issues.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 DictionaryVerb objects are preserved intact per corpus_id
- [x] #2 Stative verbs (like uksata) correctly render Set B and stative class headers
- [x] #3 Entries are not improperly merged or misclassified by definition matching
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Inspect MascotResolver and dictionary generator lookup methods to ensure exact DictionaryVerb objects are retained by corpus_id.\n2. Fix cross-reference page lookup to rely on corpus_id and exact DictionaryVerb matching instead of definition matching.\n3. Verify render_verb_minipage_community and verb_config_to_tex use verb.morphology.config, verb.morphology.class_name, and verb.original_data directly.\n4. Run tex_dictionary generator and test XeLaTeX build to confirm fixes.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Updated sorting in TeX generator to sort verbs by corpus_id, h_grade_root, glottal_grade_root, middle_voice, and definition. Retained exact DictionaryVerb objects per corpus_id to preserve stative flags, PronominalSet, and aspect class configs across both full and companion TeX generation.
<!-- SECTION:FINAL_SUMMARY:END -->
