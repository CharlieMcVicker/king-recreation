---
id: TASK-6.1
title: Migrate verified policies and general references
status: Done
assignee:
  - '@Antigravity'
created_date: '2026-06-10 16:06'
updated_date: '2026-06-10 16:11'
labels: []
dependencies: []
parent_task_id: TASK-6
ordinal: 18000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Read, review, and migrate blank-forms.md and reference/artifacts.md to backlog docs. Verify accuracy using ember and check for staleness/recency. If stale, discard instead of migrating.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Verify accuracy and recency of blank-forms.md and reference/artifacts.md
- [x] #2 Migrate valid documents to backlog docs
- [x] #3 Discard stale content
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Migrate docs/policies/blank-forms.md to backlog doc policies/blank-forms.md (accurate and active policy).\n2. Filter out stale files/paths from docs/reference/artifacts.md using dictionary_pipeline/paths.py as the source of truth, and migrate it to backlog doc guides/artifacts-reference.md.\n3. Delete the legacy files docs/policies/blank-forms.md and docs/reference/artifacts.md.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Verified blank-forms.md and artifacts.md. Created backlog doc policies/blank-forms (doc-2) with the active vacuous matching policy. Filtered out stale paths and files from artifacts.md, and created backlog doc guides/artifacts-reference (doc-3) to only list programmatically active artifacts. Deleted the legacy files docs/policies/blank-forms.md and docs/reference/artifacts.md.
<!-- SECTION:FINAL_SUMMARY:END -->
