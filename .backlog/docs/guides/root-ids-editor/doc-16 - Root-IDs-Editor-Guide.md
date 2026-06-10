---
id: doc-16
title: Root IDs Editor Guide
type: guide
created_date: '2026-06-10 16:47'
---# Root IDs Editor Guide

## Objective
Create a standalone sequential review interface for assigning and verifying `root_id` groupings in `curated/root_ids.csv`.

## Background
The `root_ids.csv` file maps a `corpus_id` to a `root_id`. The pipeline auto-generates a default `root_id` (e.g. `h_grade|g_grade`), but humans can override this. When a human edits a `root_id`, they must set `user_edited = "x"`. This ensures the pipeline respects the manual override on subsequent runs.
The goal of this editor is to allow rapid triage of unreviewed rows, or bulk editing of existing rows, grouped by their assigned `root_id`.

## Implemented Features & Routing

### 1. Routes & Layout
- **Index/Entry Point:** [page.tsx](../../../../root-based-dict/src/app/review-root-ids/page.tsx) gathers all unique `root_id` groupings present in the curated CSV, and automatically redirects the user to the first group in the sorted sequence.
- **Group Sequence Editor:** [groups/[rootIdEncoded]/page.tsx](../../../../root-based-dict/src/app/review-root-ids/groups/[rootIdEncoded]/page.tsx) identifies a specific `root_id` grouping. Slugs are base64url encoded strings to safely transfer complex IDs (like pipes or quotes) via URL routing.
- The UI is driven by the client-side component [RootGroupSequenceEditor.tsx](../../../../root-based-dict/src/components/RootGroupSequenceEditor.tsx), which provides:
  - Responsive header layout displaying the current active `root_id`, total groups, and sequence position.
  - Next/Prev navigation buttons (supporting `Left`/`Right` keyboard shortcuts).
  - A contextual "View in Dictionary" link pointing back to the main linguistic dictionary view (`/[slug]`).

### 2. The Data Display
- **Group Level Triage:** Lists all `corpus_ids` assigned to this `root_id` in a list format, displaying `definition`, `corpus_id`, `class`, `h_grade`, `g_grade`, and `post_root_morpheme`.
- **Review Status:** Visually distinguishes rows that have already been reviewed (`user_edited == "x"`).

### 3. Bulk & Sequential Editing Workflow
- Allows multi-selection of items or toggling "Select All".
- Provides a text input to supply a new `root_id` for the selected words.
- Hitting **"Apply"** sends updates to the server. Local state updates reactively. If all words in a group are moved, the UI guides the user to the next group sequence.

### 4. Dictionary Context Synchronization
- Exposes bidirectional navigation:
  - From the Dictionary detail page (`/[slug]`), an "Edit Root ID Group" button computes the shared `root_id` and navigates the user to the matching sequence editor securely (via base64url encoding).

### 5. Backend Integration
- The API endpoint [bulk/route.ts](../../../../root-based-dict/src/app/api/curated/root-ids/bulk/route.ts) handles POST requests for multiple updates, patching the corresponding `root_id` fields, setting `user_edited` to `"x"`, and saving the modified data to `curated/root_ids.csv`.
