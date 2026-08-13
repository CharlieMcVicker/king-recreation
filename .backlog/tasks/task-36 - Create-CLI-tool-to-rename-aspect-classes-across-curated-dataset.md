---
id: TASK-36
title: Create CLI tool to rename aspect classes across curated dataset
status: Done
assignee:
  - '@agent'
created_date: '2026-08-13 13:14'
updated_date: '2026-08-13 13:16'
labels: []
dependencies: []
ordinal: 62000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Implement a script scripts/rename_aspect_class.py to rename aspect classes in data/classes.csv and automatically update class references across all curated files (validated_reconstructable_roots.csv, stative_shims.csv, root_ids.csv, derivational_suffix_connections.csv, aspect_class_mascots.csv).
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Script scripts/rename_aspect_class.py exists and supports single class rename and map/batch rename
- [x] #2 Renames class names including bracketed subvariant tags in all curated CSV files
- [x] #3 Reports row counts updated per file
<!-- AC:END -->

## Implementation Plan

<!-- SECTION:PLAN:BEGIN -->
1. Create scripts/rename_aspect_class.py supporting command-line parameters for renaming single classes (--old / --new) or batch mappings (--mapping JSON/CSV).\n2. Implement regex prefix matching to update base class names and subvariant tags (e.g. old_class[perf2]) across target columns in all 5 curated CSV files as well as data/classes.csv.\n3. Add dry-run support (--dry-run) and output summary of updated rows per file.\n4. Write unit tests in tests/test_rename_aspect_class.py to verify accurate replacement behavior without unexpected side effects.\n5. Execute test suite and verify everything passes.
<!-- SECTION:PLAN:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Implemented scripts/rename_aspect_class.py CLI tool to rename aspect classes across data/classes.csv and all 5 curated dataset files (validated_reconstructable_roots.csv, stative_shims.csv, root_ids.csv, derivational_suffix_connections.csv, aspect_class_mascots.csv). Added regex prefix matching for preserving bracketed subvariants, dry-run mode (--dry-run), batch mapping support (--mapping), and unit tests in tests/test_rename_aspect_class.py.
<!-- SECTION:FINAL_SUMMARY:END -->
