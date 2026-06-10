---
id: TASK-6.2
title: Migrate verified technical specs
status: Done
assignee:
  - '@antigravity'
created_date: '2026-06-10 16:06'
updated_date: '2026-06-10 16:19'
labels: []
dependencies: []
parent_task_id: TASK-6
ordinal: 19000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Read, review, and migrate technical spec files under docs/specs/*, TeX.md, and pattern-checking-optimization.md. Verify accuracy using ember and check for staleness/recency. If stale, discard instead of migrating.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Verify accuracy and recency of specs files, TeX.md, and pattern-checking-optimization.md
- [x] #2 Migrate valid specs to backlog docs
- [x] #3 Discard stale content
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Migrate spec files (classification, h-alternation, preprocessing, reconstruction, stem-derivation) to backlog docs under specs/ namespace using backlog doc create.\n2. Merge pattern-checking-optimization.md spec details into classification spec.\n3. Migrate TeX.md to guides/tex-pipeline.\n4. Migrate root-dictionary-view.md (static details only) to guides/root-dictionary-view.\n5. Discard legacy docs files.\n6. Verify searchability using backlog search.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Migrated active specifications (classification, h-alternation, preprocessing, reconstruction, stem-derivation) to specs/ namespace in backlog docs, updating internal code links and descriptions. Merged pattern checking optimization specs into the classification specifications. Created guides for root-dictionary-view and the LaTeX print pipeline (TeX.md), and discarded all legacy documentation files. Created completed backlog tasks TASK-7 and TASK-8 representing former implementation plans.
<!-- SECTION:FINAL_SUMMARY:END -->
