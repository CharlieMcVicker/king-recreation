---
id: TASK-6.3
title: Migrate verified linguistic investigations
status: Done
assignee:
  - '@myself'
created_date: '2026-06-10 16:07'
updated_date: '2026-06-10 16:30'
labels: []
dependencies: []
parent_task_id: TASK-6
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Read, review, and migrate EXCEPTIONS.md, files under investigations/*, and tone_mvp.md. Verify accuracy using ember and check for staleness/recency. If stale, discard instead of migrating.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Verify accuracy and recency of EXCEPTIONS.md, investigations files, and tone_mvp.md
- [x] #2 Migrate valid investigations to backlog docs
- [x] #3 Discard stale content
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Update EXCEPTIONS.md content to note that 'To order' is resolved, while 'To brag' and 'To root out and boil' remain active exceptions.\n2. Migrate EXCEPTIONS.md to backlog docs at specs/exceptions using 'backlog doc create'.\n3. Migrate tone_mvp.md to backlog docs at specs/tone-analysis as 'Tone Analysis Specification', detailing inside it that the implementation represents the MVP stage.\n4. Migrate investigations/2026-01-12_general_h_plan.md to backlog docs as a sibling in specs/h-alternation/consensus-plan using 'backlog doc create'.\n5. Discard investigations/2026-01-12_short_stem_compatibility.md as it is a resolved historical debug log.\n6. Delete the legacy markdown files from the docs/ directory.\n7. Verify and mark acceptance criteria as completed.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Verified the accuracy of EXCEPTIONS.md (noting that 'To order' was resolved), tone_mvp.md (matching implementation), and investigations/2026-01-12_general_h_plan.md (matching implementation). Migrated these files to backlog docs under specs/exceptions, specs/tone-analysis, and specs/h-alternation/consensus-plan. Discarded the short stem debug log as it is historical and resolved. Removed the legacy files from the docs/ directory.
<!-- SECTION:FINAL_SUMMARY:END -->
