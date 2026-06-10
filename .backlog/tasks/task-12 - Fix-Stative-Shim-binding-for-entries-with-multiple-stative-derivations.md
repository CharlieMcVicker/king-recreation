---
id: TASK-12
title: Fix Stative Shim binding for entries with multiple stative derivations
status: Done
assignee:
  - '@agent'
created_date: '2026-06-10 18:43'
updated_date: '2026-06-10 18:43'
labels: []
dependencies: []
modified_files:
  - dictionary_pipeline/phases/select_canonical_derivations/__init__.py
priority: medium
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Resolve an issue where a stative shim was bound to the wrong stative verb derivation when a corpus ID has multiple stative verbs. Ensure the shim binds to the selected stative verb derivation.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Update save_stative_shims in select_canonical_derivations to check is_selected status (user_selected or pipeline_selected)
- [x] #2 Bind the InfEventful shim to the actual selected stative verb derivation instead of the first matched one
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Updated save_stative_shims to filter/extract the correct h-grade root from the selected stative verb derivation (checking user_selected / pipeline_selected status) when grouping and saving shims. This ensures correct stem binding in cases where a corpus ID has multiple stative derivations.
<!-- SECTION:FINAL_SUMMARY:END -->
