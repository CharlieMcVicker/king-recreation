---
id: TASK-20
title: Extract segmentation and surface forms for reconstructable verbs
status: Done
assignee:
  - '@agent'
created_date: '2026-06-29 20:31'
updated_date: '2026-06-29 20:31'
labels: []
dependencies: []
ordinal: 44000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Create a Python script that extracts segmentation lines and surface forms for each form entry stored for a reconstructable verb into a CSV in artifacts/.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Create a Python script scripts/extract_verb_forms.py
- [x] #2 The script outputs a CSV to artifacts/verb_form_segmentations.csv
- [x] #3 The CSV has columns: corpus_id, form_name, surface, segmented
- [x] #4 Verify that the output contains all expected reconstructable verb entries
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Created scripts/extract_verb_forms.py which loads reconstructable verbs from JSON, collects all unique verbs recursively, extracts their segmented forms, converts them to surface forms using the morphology desegmentation logic, and saves the output to artifacts/verb_form_segmentations.csv with the columns corpus_id, form_name, surface, segmented.
<!-- SECTION:FINAL_SUMMARY:END -->
