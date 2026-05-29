---
id: TASK-2.1
title: Split loading of class patterns for stative/eventful verbs
status: To Do
assignee: []
created_date: '2026-05-29 13:16'
labels:
  - debt
dependencies: []
parent_task_id: TASK-2
priority: medium
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Refactor the class pattern loading logic to separate stative and eventful verbs, and eliminate bad singleton patterns.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Loading logic for class patterns is refactored into distinct pipelines or handlers for stative and eventful verbs
- [ ] #2 Singleton instances that hold global state for class patterns are removed or replaced with safe context/dependency injection
- [ ] #3 Existing unit tests pass and new tests verify independent loading of stative and eventful class patterns
<!-- AC:END -->
