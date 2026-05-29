---
id: TASK-1.1
title: Update Pipeline and Backend to Resolve and Embed Stative Shims
status: Done
assignee: []
created_date: '2026-05-29 13:15'
updated_date: '2026-05-29 13:48'
labels:
  - feature
dependencies: []
parent_task_id: TASK-1
priority: medium
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Extend the dictionary pipeline and Next.js backend data layers to support linking FullStative verbs with InfEventful shims:
1. Define a curation CSV curated/stative_shims.csv schema to store human-approved stative shim selections.
2. Update Next.js data-shared.ts to include InfEventful in the Prediction enum and add shim?: ReconstructableVerb to ReconstructableVerb.
3. Update select_canonical_derivations to identify InfEventful shims for FullStative canonical choices (looking up overrides in curated/stative_shims.csv or falling back to deterministic heuristics), nesting the selected shim inside the shim field of the DictionaryVerb and saving it to reconstructable_verbs.json.
4. Implement data helpers in data.ts to load/write curated/stative_shims.csv.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 validated_reconstructable_roots.csv and curated/stative_shims.csv are parsed cleanly by the Next.js data layer
- [ ] #2 Prediction enum in data-shared.ts includes InfEventful and ReconstructableVerb supports shim field
- [ ] #3 select_canonical_derivations successfully outputs nested shim structures to reconstructable_verbs.json
- [ ] #4 Unit tests verify pipeline resolution and serialization of stative shims
<!-- AC:END -->
