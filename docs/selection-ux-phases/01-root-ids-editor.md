# Phase: Root IDs Editor

## Objective

Create a standalone sequential review interface for assigning and verifying `root_id` groupings in `curated/root_ids.csv`.

## Background

The `root_ids.csv` file maps a `corpus_id` to a `root_id`. The pipeline auto-generates a default `root_id` (e.g. `h_grade|g_grade`), but humans can override this. When a human edits a `root_id`, they must set `user_edited = "x"`. This ensures the pipeline respects the manual override on subsequent runs.
The goal of this editor is to allow rapid triage of unreviewed rows, or bulk editing of existing rows, grouped by their assigned `root_id`.

## Features & Requirements

### 1. Route & Layout

- **Index/Entry Point (`/review-root-ids`)**: Gather all unique `root_id` groupings present in the curated CSV, and automatically redirect the user to the first group in the sorted sequence.
- **Group Sequence Editor (`/review-root-ids/groups/[rootIdEncoded]`)**: A specialized Next.js route that identifies a specific `root_id` grouping. Slugs are base64url encoded strings to safely transfer complex IDs (like pipes or quotes) via URL routing.
- Provide a responsive header layout:
  - Display the current active `root_id` as the title.
  - Display total groups and sequence position.
  - Next/Prev arrow buttons (with `Left`/`Right` keyboard shortcuts) to step through groups.
  - A contextual **"View in Dictionary"** link pointing back to the main linguistic dictionary view (`/[slug]`), powered by calculating which reconstructable root encompasses the current verbs.

### 2. The Data Display

- **Group Level Triage:** View all `corpus_ids` assigned to this `root_id` in a list format.
- For each item, display: `definition`, `corpus_id`, `class`, `h_grade`, `g_grade`, and `post_root_morpheme`.
- **Review Status:** Visually distinguish rows that have already been reviewed (`user_edited == "x"`).

### 3. Bulk & Sequential Editing Workflow

- **Multi-select items:** Select specific verbs, or toggle "Select All", to target them for editing.
- **Target `root_id` input:** Provide a text input to supply a new `root_id` for the selected words.
- Hitting **"Apply"** sends the selected `corpus_id`s and the new `root_id` to the server.
- _Reactivity:_ Once the bulk update resolves, the local state is updated to reflect the new `root_id` assignments. If all words in a group were removed (moved to another group), the UI gracefully guides the user to the Next Group sequence.

### 4. Dictionary Context Synchronization

- Expose bidirectional navigation to link the data curation step directly to its linguistic outcome:
  - From the Dictionary detail (`/[slug]`), expose an **"Edit Root ID Group"** button that computes the shared `root_id` and navigates the user to the matching sequence editor securely (via base64url encoding).

### 5. Backend Integration

- Implemented an API endpoint (`/api/curated/root-ids/bulk`) to handle POST requests encompassing multiple updates.
- The endpoint maps over the requested arrays of object updates, identifies matches in `/curated/root_ids.csv`, patches the corresponding `root_id` fields, sets `user_edited` to `"x"`, and flushes the modified data safely to disk.
