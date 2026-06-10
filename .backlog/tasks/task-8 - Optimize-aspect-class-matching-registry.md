---
id: TASK-8
title: Optimize aspect class matching registry
status: Done
assignee: []
created_date: '2026-06-10 16:16'
labels: []
dependencies: []
ordinal: 24000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Optimize aspect class matching by replacing the O(N*M) check loop with a PatternRegistry using a reverse-lookup map of endings.
<!-- SECTION:DESCRIPTION:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Introduced ClassMacro, ExpandedClassPattern, and PatternRegistry to index class patterns by their endings, reducing aspect class identification runtime from O(N*M) to a fast suffix lookup.
<!-- SECTION:FINAL_SUMMARY:END -->
