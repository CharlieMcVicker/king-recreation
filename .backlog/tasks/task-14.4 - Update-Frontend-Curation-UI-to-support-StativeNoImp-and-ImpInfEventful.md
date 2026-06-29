---
id: TASK-14.4
title: Update Frontend Curation UI to support StativeNoImp and ImpInfEventful
status: In Progress
assignee:
  - '@myself'
created_date: '2026-06-22 20:04'
updated_date: '2026-06-22 20:09'
labels: []
dependencies: []
parent_task_id: TASK-14
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update the React/Next.js frontend curation views to support the new prediction enums: treat StativeNoImp as a stative base verb (like FullStative), and treat ImpInfEventful as an eventful shim candidate (like InfEventful).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Frontend recognizes StativeNoImp as a valid stative base prediction type
- [ ] #2 Frontend recognizes ImpInfEventful as a valid eventful shim prediction type
- [ ] #3 Shim review page correctly filters, groups, and compares StativeNoImp and ImpInfEventful pairs
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Update Prediction enum in data-shared.ts to include StativeNoImp and ImpInfEventful.\n2. Filter out Prediction.ImpInfEventful in getValidatedRootsRows in data.ts.\n3. Update isStative in CorpusTable.tsx to recognize Prediction.StativeNoImp.\n4. Update ReviewStativeShimsPage in page.tsx to recognize StativeNoImp as stative base and ImpInfEventful as shim candidate.
<!-- SECTION:PLAN:END -->
