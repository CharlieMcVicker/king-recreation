---
id: TASK-4.5
title: 'TASK-4.5 - Backend: Implement Don''t-Care Logic for Unused/Undefined Shim Flags'
status: To Do
assignee: []
created_date: '2026-05-29 14:12'
updated_date: '2026-05-29 14:14'
labels: []
dependencies:
  - TASK-4.4
modified_files:
  - dictionary_pipeline/phases/select_canonical_derivations/__init__.py
parent_task_id: TASK-4
priority: medium
ordinal: 15000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Scope and implement a 'dont-care' matching strategy for pronominal configuration flags (such as uwa_v, ka_variant) that are undefined or not used in either the stative base derivation or the shim candidate. This task focuses on loose matching when certain configuration details are missing or cannot be determined.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Implement logic to ignore differences in config flags that are marked as undefined/unused/null.
- [ ] #2 Ensure that missing values in uwa_v or ka_variant do not block joining a candidate shim.
- [ ] #3 Unit tests verify that shims join successfully when undefined flags differ.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. In `dictionary_pipeline/phases/select_canonical_derivations/__init__.py`, update the `validate_shim_compatibility` logic:
   - Identify which pronominal config flags are unused or cannot be determined in the current derivations (specifically focus on `uwa_v`, `ka_variant`, and possibly others).
   - Implement a "don't-care" evaluation: if a flag is not defined, or if either side does not explicitly assert it, ignore differences in that flag between the stative base verb and the candidate shim.
2. Update backend unit tests to verify:
   - Shims are successfully joined even if their `uwa_v` or `ka_variant` flags differ, provided the rest of the strict rules match.
   - The validation doesn't throw false positives on these undefined flags.
<!-- SECTION:PLAN:END -->
