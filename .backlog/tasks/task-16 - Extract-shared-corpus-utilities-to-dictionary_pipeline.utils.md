---
id: TASK-16
title: Extract shared corpus utilities to dictionary_pipeline.utils
status: In Progress
assignee:
  - '@subagent'
created_date: '2026-06-29 17:36'
updated_date: '2026-06-29 17:39'
labels: []
dependencies: []
modified_files:
  - dictionary_pipeline/utils/__init__.py
  - dictionary_pipeline/utils/text.py
  - dictionary_pipeline/utils/io.py
  - dictionary_pipeline/phases/preprocess_ced/__init__.py
  - dictionary_pipeline/phases/preprocess_ced/artifacts.py
  - dictionary_pipeline/tone/utils.py
  - noun_pipeline/phases/create_corpus/__init__.py
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Refactor and standardize shared utilities between dictionary_pipeline and noun_pipeline.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Create dictionary_pipeline/utils/ as a directory package with __init__.py
- [x] #2 Move text cleaning functions (clean_string, respell_consonants) to dictionary_pipeline/utils/text.py
- [x] #3 Move read_original_cnd to dictionary_pipeline/utils/io.py
- [x] #4 Update references in dictionary_pipeline/phases/preprocess_ced/__init__.py and noun_pipeline/phases/create_corpus/__init__.py
- [x] #5 Run uv run pytest to verify the codebase remains healthy
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Create dictionary_pipeline/utils/ package\n2. Move text cleaning functions\n3. Move I/O functions\n4. Update references\n5. Run tests
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Refactored and extracted shared corpus utilities to dictionary_pipeline.utils. Created utils/ package with text.py (clean_string, respell_consonants) and io.py (read_original_cnd). Updated references across dictionary_pipeline and noun_pipeline, and successfully verified all tests pass.
<!-- SECTION:FINAL_SUMMARY:END -->
