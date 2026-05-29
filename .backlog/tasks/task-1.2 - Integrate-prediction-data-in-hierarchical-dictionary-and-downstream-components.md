---
id: TASK-1.2
title: Build Standalone Sequential Review UX and Update Dictionary Rendering
status: To Do
assignee: []
created_date: '2026-05-29 13:15'
updated_date: '2026-05-29 13:23'
labels:
  - feature
dependencies: []
parent_task_id: TASK-1
priority: medium
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Design and implement the frontend review flow and dictionary display updates for stative shims:
1. Implement a Next.js API endpoint /api/curated/stative-shims to handle POST requests from the UI and write selections to curated/stative_shims.csv.
2. Build a standalone sequential review page /review-stative-shims (with left/right keyboard navigation) that displays the FullStative verb on the left and the candidate InfEventful shims with matching h_grade roots on the right.
3. Include a selection interface to bind a shim to the stative verb and save via the API.
4. Update CorpusTable.tsx to read verb.shim and render the infinitive form from the nested shim instead of the hardcoded ∅ (Stative) text when a shim is bound.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Standalone sequential review interface is accessible at /review-stative-shims and displays correct unreviewed Stative entries
- [ ] #2 Selection interface shows only shims with matching h_grade roots
- [ ] #3 Saving a selection successfully updates curated/stative_shims.csv via the API endpoint
- [ ] #4 CorpusTable.tsx displays the infinitive form from the nested shim if it exists for a FullStative entry
- [ ] #5 Sequential review header displays correct reviewed/total count and Unreviewed Only filter works properly
<!-- AC:END -->
