---
id: TASK-15
title: Update Frontend Curation UI to support StativeNoImp and ImpInfEventful
status: To Do
assignee: []
created_date: '2026-06-22 20:03'
labels: []
dependencies: []
ordinal: 34000
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
