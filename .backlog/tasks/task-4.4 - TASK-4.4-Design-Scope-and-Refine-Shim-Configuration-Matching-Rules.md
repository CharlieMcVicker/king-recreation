---
id: TASK-4.4
title: 'TASK-4.4 - Design: Scope and Refine Shim Configuration Matching Rules'
status: Done
assignee: []
created_date: '2026-05-29 14:10'
updated_date: '2026-05-29 17:01'
labels: []
dependencies: []
documentation:
  - curated/stative_shims.csv
  - curated/validated_reconstructable_roots.csv
  - dictionary_pipeline/phases/select_canonical_derivations/__init__.py
parent_task_id: TASK-4
priority: medium
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Scope and refine the configuration matching rules between FullStative verbs and InfEventful shims. Set type (set_a_b) must be allowed to differ (e.g. stative uses Set B, shim uses Set A). Suffix class and post-root morpheme must NOT match. Add a note that g_grade is sticky: it often cannot be derived and is null for one or both derivations, so it should be handled gracefully (e.g., matching when either is null or using a fallback check). Note: Don't-Care logic for unused/undefined flags like uwa_v and ka_variant is deferred to TASK-4.5.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A finalized document or code spec defining compatibility rules between base stative verbs and shims (excluding suffix class, post-root morphemes, and set_type).
- [ ] #2 Graceful handling of g_grade is defined (recognizing it is often null for one or both derivations).
- [ ] #3 Documented that aspect suffix class and post-root morphemes must NOT be matched.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Implemented as code spec via `validate_shim_compatibility()` in `dictionary_pipeline/phases/select_canonical_derivations/__init__.py`.

Compatibility rules:
- glottal_grade_root: must match unless either side is None (graceful handling for sticky g_grade)
- middle_voice: must match
- plural_pronouns: must match
- suffix class (class_name): NOT matched — shim uses its own eventive class
- post_root_morpheme: NOT matched
- set_type (set_a_b): NOT matched — allows Set A shim with Set B stative
- uwa_v, ka_variant: deferred to TASK-4.5 (don't-care for undefined flags)
<!-- SECTION:PLAN:END -->
