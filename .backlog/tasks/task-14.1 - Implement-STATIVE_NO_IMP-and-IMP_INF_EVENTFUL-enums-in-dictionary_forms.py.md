---
id: TASK-14.1
title: Implement STATIVE_NO_IMP and IMP_INF_EVENTFUL enums in dictionary_forms.py
status: Done
assignee:
  - '@myself'
created_date: '2026-06-22 15:52'
updated_date: '2026-06-22 15:55'
labels: []
dependencies: []
modified_files:
  - dictionary_pipeline/dictionary_forms.py
parent_task_id: TASK-14
priority: medium
ordinal: 31000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Define STATIVE_NO_IMP and IMP_INF_EVENTFUL in the Prediction enum, update RowPredictionsSpec, FORM_NAME_TO_ASPECT_FOR_PREDICTION, and other configuration dictionaries in dictionary_forms.py.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Prediction enum includes STATIVE_NO_IMP and IMP_INF_EVENTFUL
- [x] #2 ROW_PREDICTION_SPECS matches StativeNoImp rows
- [x] #3 FORM_NAME_TO_ASPECT_FOR_PREDICTION maps aspects correctly for both new enums
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Define STATIVE_NO_IMP = "StativeNoImp" and IMP_INF_EVENTFUL = "ImpInfEventful" in the Prediction enum class in dictionary_forms.py.\n2. Add StativeNoImp configuration to ROW_PREDICTION_SPECS.\n3. Update PREDICTION_IS_STATIVE, FORM_NAME_TO_ASPECT_FOR_PREDICTION, and FORM_NAMES_FOR_PREDICTION configuration dictionaries.\n4. Verify changes.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Defined STATIVE_NO_IMP and IMP_INF_EVENTFUL in the Prediction enum class. Added StativeNoImp configuration to ROW_PREDICTION_SPECS. Updated PREDICTION_IS_STATIVE, FORM_NAME_TO_ASPECT_FOR_PREDICTION, and FORM_NAMES_FOR_PREDICTION.
<!-- SECTION:FINAL_SUMMARY:END -->
