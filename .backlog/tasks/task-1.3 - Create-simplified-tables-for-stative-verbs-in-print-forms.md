---
id: TASK-1.3
title: Create simplified tables for stative verbs in print forms
status: To Do
assignee: []
created_date: '2026-05-29 13:15'
updated_date: '2026-06-10 17:02'
labels:
  - feature
dependencies: []
parent_task_id: TASK-1
priority: medium
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Generate simplified tabular representations for stative verbs suitable for print dictionary layouts.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Stative verb print layout generator creates simplified tables
- [ ] #2 Table format matches print design guidelines
- [ ] #3 Visual verification passes for generated sample PDFs/documents
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Currently, the print dictionary generator (tex_dictionary/generator.py) unconditionally displays all 6 standard forms for every verb. This task remains open to create simplified tables that omit/format empty stative verb forms (infinitive/imperative) in the print dictionary.
<!-- SECTION:NOTES:END -->
