---
id: TASK-10
title: Document and enforce Canonical Derivation constraints
status: Done
assignee:
  - '@agent'
created_date: '2026-06-10 18:42'
updated_date: '2026-06-10 18:42'
labels: []
dependencies: []
modified_files:
  - >-
    .backlog/docs/specs/reconstruction/doc-7 -
    Reconstruction-from-Roots-Specification.md
  - root-based-dict/src/lib/data.ts
  - root-based-dict/src/app/review-stative-shims/page.tsx
  - root-based-dict/src/components/SelectRootsWorkflow.tsx
priority: medium
ordinal: 26000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Limit canonical derivations to FullStative and FullEventful aspect predictions, excluding shims like InfEventful. Ensure the pipeline and frontend selection interface align with this constraint.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Update Reconstruction-from-Roots-Specification.md to document canonical derivation constraints
- [x] #2 Update frontend data selectors (getValidatedRootsRows) to exclude InfEventful predictions unless shims are explicitly requested
- [x] #3 Update frontend workflow components (SelectRootsWorkflow) to map index selections using originalIndex to avoid selection drift
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Documented in Reconstruction-from-Roots-Specification.md that canonical derivations are restricted to FullStative and FullEventful predictions. Implemented filtering in the frontend data layer (getValidatedRootsRows) to exclude InfEventful unless explicitly requested, and updated components to use originalIndex to prevent selection drift.
<!-- SECTION:FINAL_SUMMARY:END -->
