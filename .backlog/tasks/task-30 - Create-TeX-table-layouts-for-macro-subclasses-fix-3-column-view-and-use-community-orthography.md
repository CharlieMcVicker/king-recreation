---
id: TASK-30
title: >-
  Create TeX table layouts for macro/subclasses, fix 3-column view, and use
  community orthography
status: Done
assignee:
  - '@agent-k'
created_date: '2026-08-12 13:33'
updated_date: '2026-08-12 13:36'
labels: []
dependencies: []
priority: high
ordinal: 56000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Update TeX macro class output to display table of forms for sample word and per-subclass form/matching tables, fix 3-column layout rendering (currently shows bare '3'), and fix orthography conversion to use community orthography rather than internal/Linguistic orthography.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each macro class renders a table of forms for the sample word
- [x] #2 Each subclass renders a table for its 1st subclass forms and matching words table for 2nd subclass
- [x] #3 3-column view renders correctly in TeX output without bare '3'
- [x] #4 TeX generator uses Community orthography (e.g. no raw HS sequences or TH in segments)
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Inspect TeX generator module and orthography conversion modules.\n2. Fix 3-column view rendering bug (remove/fix bare '3').\n3. Update orthography pipeline to ensure Community orthography is applied (fix 'HS' sequences and 'TH' in segments).\n4. Update macro class formatting to render a table of forms for sample word.\n5. Update subclass formatting: render table of forms for 1st subclass and list of matching words table for 2nd subclass.\n6. Verify LaTeX output and run tests.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Updated TeX macro class tables and companion generators: fixed 3-column multicols layout by correcting \begin{multicol} to \begin{multicols}, enforced community orthography rules across all TeX generators, updated macro class tables to render 6-form tables for sample words, and updated subclass TeX rendering to produce a table of forms for the 1st subclass and a list of matching words for subsequent subclasses. All 100 pytest unit tests passed cleanly.
<!-- SECTION:FINAL_SUMMARY:END -->
