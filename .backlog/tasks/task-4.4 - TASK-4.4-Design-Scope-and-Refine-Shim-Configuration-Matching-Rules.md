---
id: TASK-4.4
title: 'TASK-4.4 - Design: Scope and Refine Shim Configuration Matching Rules'
status: To Do
assignee: []
created_date: '2026-05-29 14:10'
updated_date: '2026-05-29 14:13'
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
1. Write a design document or draft the validation function specification detailing the matching criteria:
   - Root Grades: `h_grade` and `g_grade` must match.
     - *Handle g_grade gracefully*: Since `g_grade` often cannot be derived and is null for either or both derivations (stative/shim), the matching logic must handle missing values gracefully (e.g. treated as compatible if either grade is empty/null/None).
   - Pronominal Config: `middle_voice` and `plural` (plural pronouns) must match.
   - Suffix Class & Morpheme: Suffix `class` and `post_root_morpheme` MUST NOT be matched. The shim is explaining the eventive infinitive form, which cannot be explained by the stative class.
   - Set Type: `set_a_b` / `set_type` MUST NOT be matched, allowing Set A (shim) vs Set B (stative) divergence.
2. Note that "Don't-Care" logic (loose matching when unused/undefined flags like `uwa_v` or `ka_variant` differ) is split into its own task (TASK-4.5) to be done as a separate, later ticket.
<!-- SECTION:PLAN:END -->
