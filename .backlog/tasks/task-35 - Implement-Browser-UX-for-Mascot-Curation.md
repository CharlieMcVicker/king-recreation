---
id: TASK-35
title: Implement Browser UX for Mascot Curation
status: Done
assignee:
  - '@agent-k'
created_date: '2026-08-12 16:34'
updated_date: '2026-08-12 16:47'
labels: []
dependencies: []
ordinal: 61000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend root-based-dict web app with a browser-based Mascot Curation UX for selecting and persisting mascot_corpus_id per aspect class in curated/aspect_class_mascots.csv.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Display list of 50 verb paradigm classes and their current mascots
- [x] #2 Provide search/picker interface to select candidate corpus_id for each class
- [x] #3 Persist selected mascot assignments to curated/aspect_class_mascots.csv
- [x] #4 Integrate preview/validation of 6-form mascot table
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Simplify aspect class listing to extract all unique morphology.class_name strings directly from hierarchical-dict.json (via getRoots()).\n2. Left sidebar displays exact class_name strings (e.g. i-a-i, become, sk-s-a, apl[imp3], etc.).\n3. Right panel lists all candidate verbs whose morphology.class_name matches the selected class string.\n4. Selecting a candidate verb sets mascot_corpus_id and saves to curated/aspect_class_mascots.csv.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Updated candidate extraction logic in root-based-dict/src/app/api/mascots/route.ts to traverse hierarchical-dict.json (via getRoots()) recursively including derivations. Verbs and candidates are now strictly filtered and counted by their true morphology.class_name rather than raw validated_roots.csv rows. Verified candidate search and 6-form paradigm preview fetching for classes like 'become' and 'cause'. Ran production build (npm run build) successfully.
<!-- SECTION:FINAL_SUMMARY:END -->
