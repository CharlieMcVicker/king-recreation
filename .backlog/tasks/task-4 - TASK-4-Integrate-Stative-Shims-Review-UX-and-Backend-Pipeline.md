---
id: TASK-4
title: TASK-4 - Integrate Stative Shims Review UX and Backend Pipeline
status: In Progress
assignee: []
created_date: '2026-05-29 14:06'
updated_date: '2026-06-10 16:54'
labels: []
dependencies: []
parent_task_id: TASK-1
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

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
Move the task 'TASK-4 - Integrate Stative Shims Review UX and Backend Pipeline' to be a subtask of 'TASK-1 - Prediction scoping'.

**Justification:**
TASK-4 directly implements a significant portion of the 'stative and eventful verb form merging' aspect of TASK-1. The work on stative shims is a concrete step towards achieving the broader goal of prediction scoping. The existing subtasks of TASK-4 are also focused on refining and implementing this specific part of the prediction scoping feature. This re-parenting will better reflect the hierarchical relationship and dependencies between these tasks.
<!-- SECTION:PLAN:END -->
