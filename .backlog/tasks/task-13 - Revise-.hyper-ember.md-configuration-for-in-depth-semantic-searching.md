---
id: TASK-13
title: Revise .hyper-ember.md configuration for in-depth semantic searching
status: Done
assignee:
  - '@myself'
created_date: '2026-06-22 13:08'
updated_date: '2026-06-22 13:11'
labels: []
dependencies: []
ordinal: 29000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Revise the .hyper-ember.md configuration file to map out all project directories and directories containing key documentation, specs, codebases, and scripts, enabling hyper-ember to perform highly accurate semantic searches across the repository.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Generate or update .hyper-ember.md using hyper-ember --create-config
- [x] #2 Review and refine directory mappings and descriptions in .hyper-ember.md
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Run hyper-ember --create-config to generate base mapping configuration.\n2. Inspect the generated configuration.\n3. Revise and enrich .hyper-ember.md to map all critical project directories (morphology, dictionary_pipeline, tex_dictionary, web_viewer, .backlog/docs, scripts, tests, data) with detailed descriptions of their contents.\n4. Verify the configuration by testing a query with hyper-ember.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Revised the .hyper-ember.md configuration mapping directory structure to enable in-depth semantic searching. Added detailed and precise description mappings for all modules (morphology, dictionary_pipeline, root-based-dict, tex_dictionary, web_viewer, tests, data, curated, and .backlog/docs). Cleaned up obsolete directories and verified the configuration by running a test hyper-ember query.
<!-- SECTION:FINAL_SUMMARY:END -->
