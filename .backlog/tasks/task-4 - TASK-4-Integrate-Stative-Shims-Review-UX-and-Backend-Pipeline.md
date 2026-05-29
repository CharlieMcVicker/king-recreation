---
id: TASK-4
title: TASK-4 - Integrate Stative Shims Review UX and Backend Pipeline
status: To Do
assignee: []
created_date: '2026-05-29 14:06'
updated_date: '2026-05-29 14:10'
labels: []
dependencies: []
documentation:
  - curated/stative_shims.csv
  - curated/validated_reconstructable_roots.csv
  - dictionary_pipeline/phases/select_canonical_derivations/__init__.py
  - root-based-dict/src/components/ReviewStativeShims.tsx
  - root-based-dict/src/components/SelectRootsWorkflow.tsx
priority: medium
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement the review UX and backend verification pipeline for Cherokee stative verb shims. This includes aligning the shims storage structure with validated roots, scoping and enforcing configuration matching rules between stative base verbs and InfEventful shims, and building a side-by-side diffed comparison table in the Next.js review interface.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Parent task tracking the implementation of the stative shims review UX and backend validation pipeline.
<!-- AC:END -->
