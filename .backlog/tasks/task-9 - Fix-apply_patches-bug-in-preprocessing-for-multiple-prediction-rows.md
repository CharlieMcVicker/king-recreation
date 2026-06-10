---
id: TASK-9
title: Fix apply_patches bug in preprocessing for multiple prediction rows
status: Done
assignee:
  - '@agent'
created_date: '2026-06-10 17:46'
updated_date: '2026-06-10 18:43'
labels: []
dependencies: []
ordinal: 25000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The preprocessor's apply_patches logic builds a data_map from corpus_id to row. Because multiple prediction rows share a corpus_id, the map overwrites entries, corrupting the INF_EVENTFUL predictions when a manual correction specifies 'FullStative'. We need to fix apply_patches to support multiple rows, and handle prediction overrides at row-generation time.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Avoid using dict comprehension to overwrite multiple rows with same corpus_id in apply_patches
- [x] #2 Allow prediction override during create_corpus_from_cn_dict row generation
- [x] #3 Write unit test for end-to-end matching of corpus row 729 'wearing glasses'
- [x] #4 Run full pipeline successfully and verify test passes
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Avoided dict comprehension in apply_patches to prevent overwriting rows with the same corpus_id. Implemented prediction overrides during row generation using the manual corrections map. Added a unit test in tests/test_wearing_glasses.py to verify end-to-end matching for corpus row 729 ('wearing glasses'), and verified that the full pipeline runs successfully and all tests pass.
<!-- SECTION:FINAL_SUMMARY:END -->
