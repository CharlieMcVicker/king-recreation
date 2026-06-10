---
id: TASK-4.3
title: >-
  TASK-4.3 - Frontend: Restrict Candidates and Implement Diffed Comparison Table
  for Shims
status: Done
assignee: []
created_date: '2026-05-29 14:07'
updated_date: '2026-06-10 17:07'
labels: []
dependencies:
  - TASK-4.1
  - TASK-4.4
documentation:
  - root-based-dict/src/components/ReviewStativeShims.tsx
  - root-based-dict/src/components/SelectRootsWorkflow.tsx
modified_files:
  - root-based-dict/src/components/ReviewStativeShims.tsx
  - root-based-dict/src/app/review-stative-shims/page.tsx
  - root-based-dict/src/app/api/curated/stative-shims/route.ts
  - root-based-dict/src/lib/data.ts
parent_task_id: TASK-4
priority: medium
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update the Next.js Review Stative Shims page and ReviewStativeShims component to render a side-by-side diffed comparison table of candidate shims, modeled after SelectRootsWorkflow. Restrict the list of candidate shims shown to the user based on the matching criteria scoped in TASK-4.4 (excluding suffix class and post-root morpheme, and allowing set_type divergence). Update the API route (/api/curated/stative-shims) to write selection markers to the new csv structure.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The Review Stative Shims UI shows a tabular comparison of all candidate shims.
- [x] #2 Redundant fields (where all candidates have the same value) can be hidden with a toggle button, exactly like the SelectRootsWorkflow component.
- [x] #3 Different values between the selected/focused candidate and other options are highlighted (diffed).
- [x] #4 Only shims matching the scoped configuration criteria for the base derivation are shown as options.
- [x] #5 Saving a selection writes an "x" to user_selected in the new csv format via /api/curated/stative-shims API route.
- [x] #6 UI features responsive, premium styling matching existing Next.js layout guidelines.
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. In `root-based-dict/src/lib/data.ts`, update `getStativeShims` and `updateStativeShim` to read and write rows using the new schema layout (with all candidates and curation selection columns).
2. In `root-based-dict/src/app/review-stative-shims/page.tsx`, fetch candidate shims directly from the new CSV structure, filtering to candidates compatible with the base stative verb according to TASK-4.4 rules.
3. In `root-based-dict/src/components/ReviewStativeShims.tsx`, design a side-by-side comparison table of candidate shims:
   - Make the candidates' features side-by-side (Choice 1, Choice 2, etc.), similar to `SelectRootsWorkflow.tsx`.
   - Highlight value differences (diffs) between the selected/focused choice and other options in amber.
   - Implement a toggle button to show/hide redundant/identical rows (e.g. fields that are identical across all candidates) to declutter the layout.
   - Bind keyboard navigation (left/right to navigate verbs, Enter to save, focus selection).
4. Update the endpoint `/api/curated/stative-shims` in `root-based-dict/src/app/api/curated/stative-shims/route.ts` to receive selection updates and mark `user_selected = "x"` in the new csv format.
5. Manually verify the UI locally in the browser, testing the side-by-side table, toggle button, keyboard shortcuts, and saving selections.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented restricted shim candidates list in page.tsx and designed a premium, side-by-side diffed comparison table in ReviewStativeShims.tsx with a redundant rows toggle, keyboard navigation, and unbind support.
<!-- SECTION:FINAL_SUMMARY:END -->
