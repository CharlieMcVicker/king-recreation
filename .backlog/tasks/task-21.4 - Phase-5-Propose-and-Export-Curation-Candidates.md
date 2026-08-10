---
id: TASK-21.4
title: 'Phase 5: Propose and Export Curation Candidates'
status: To Do
assignee: []
created_date: '2026-06-29 22:18'
updated_date: '2026-06-30 18:51'
labels: []
dependencies: []
parent_task_id: TASK-21
ordinal: 49000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Score and output the best deverbal root matches into a curation CSV (artifacts/corpora/noun_curation_candidates.csv) for human review.

The candidates should be classified under a descriptive `match_type` enum:
- `both_direct`: Both singular and plural validated, direct root match.
- `both_reconstruction`: Both singular and plural validated, reconstruction match.
- `single_direct`: Singular only validated, direct root match.
- `single_reconstruction`: Singular only validated, reconstruction match.

Sort candidates by validation strength (both_direct > both_reconstruction > single_direct > single_reconstruction).
<!-- SECTION:DESCRIPTION:END -->
