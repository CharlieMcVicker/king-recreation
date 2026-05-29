---
id: TASK-3
title: >-
  Investigate why InfEventful verbs are not reaching validated reconstruction
  stage
status: Done
assignee:
  - Antigravity
created_date: '2026-05-29 13:48'
updated_date: '2026-05-29 14:06'
labels: []
dependencies: []
modified_files:
  - dictionary_pipeline/phases/analyze_pipeline_run/__init__.py
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Explore the pipeline phases, specifically preprocess_ced and reconstruct_and_validate, to understand why InfEventful predictions/stems are missing or dropping out before the validated reconstruction stage.
<!-- SECTION:DESCRIPTION:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Grouped furthest corpus status report by both corpus_id and prediction to allow tracking individual predictions (e.g. InfEventful) through validation.

Ran full pipeline to regenerate report and verify the changes. The report successfully shows different results per prediction under the same corpus ID.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Identified that InfEventful predictions were dropping out because the aspect classification match step was validating all 5 aspect forms against the eventful class endings (which failed on the stative present/imperfective/perfective/imperative forms of the verbs). Updated aspect classification to only check forms in the active prediction's scope. Additionally, filtered the verb coverage metrics to only count major predictions (FullEventful and FullStative) to avoid artificial inflation by auxiliary InfEventful predictions.
<!-- SECTION:FINAL_SUMMARY:END -->
