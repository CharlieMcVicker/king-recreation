---
id: TASK-6
title: Migrate stale /docs directory to Backlog.md
status: Done
assignee: []
created_date: '2026-06-10 16:02'
updated_date: '2026-06-10 16:48'
labels: []
dependencies: []
ordinal: 17000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Migrate all documents from the legacy /docs directory into modular, bite-sized, and cross-referenced backlog docs according to the Backlog Documentation Standards (doc-1). For each file read and reviewed, verify both its accuracy in its description of the codebase (using ember to search for relevant code) as well as its staleness/recency. Stale data must not be moved to backlog docs.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All subtasks for migrating and verifying legacy /docs are complete
- [x] #2 Legacy /docs directory is removed
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Refactor doc-1 to be purely the Backlog Documentation Standards.\n2. Migrate policies/blank-forms.md and reference/artifacts.md to backlog docs.\n3. Migrate specs/ files, TeX.md, and pattern-checking-optimization.md to backlog docs.\n4. Migrate EXCEPTIONS.md, investigations/ files, and tone_mvp.md to backlog docs.\n5. Migrate selection-ux-phases/ and aspect_class_companion/ to backlog docs.\n6. Verify all references and delete the legacy /docs directory.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Successfully completed all subtasks to migrate verified, accurate policies, specs, investigations, plans, and guides from the legacy /docs directory into backlog documents. Discarded stale/historic content and deleted the legacy /docs directory.
<!-- SECTION:FINAL_SUMMARY:END -->
