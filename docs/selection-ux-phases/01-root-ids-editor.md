# Phase: Root IDs Editor

## Objective

Create a standalone sequential review interface for assigning and verifying `root_id` groupings in `curated/root_ids.csv`.

## Background

The `root_ids.csv` file maps a `corpus_id` to a `root_id`. The pipeline auto-generates a default `root_id` (e.g. `h_grade|g_grade`), but humans can override this. When a human edits a `root_id`, they must set `user_edited = "x"`. This ensures the pipeline respects the manual override on subsequent runs.
The goal of this editor is to allow rapid triage of unreviewed rows, or bulk editing of existing rows.

## Features & Requirements

### 1. Route & Layout

- Create a new Next.js route: `/review-root-ids`.
- Provide a header similar to the existing `/select-roots` workflow:
  - Display the current word's `definition`.
  - Display the `corpus_id`.
  - Show traversal progress (e.g., `45 / 600 reviewed`).
  - Next/Prev arrow buttons (with `Left`/`Right` keyboard shortcuts).

### 2. The Data Display

- **Current Word Details:** Display the `h_grade`, `g_grade`, `class`, and `post_root_morpheme` for the focused `corpus_id`.
- **Primary Action (Input):** Render a text input focused on the `root_id`.
  - By default, it shows the current `root_id`.
  - The user can type a new `root_id`.
  - Hitting `Enter` saves the assignment and auto-advances to the next word.

### 3. Contextual Grouping (The "Sibling" List)

- To help the user understand why a `root_id` is assigned, the UI **must** display a list or table of _all other words in the dataset_ that currently share the same `root_id`.
- For example, if the current word has `root_id = "a|a"`, query the dataset for all other `corpus_ids` where `root_id == "a|a"` and display their definitions, corpus IDs, and forms below the main input.
- _Reactivity:_ If the user types a new `root_id` in the input (e.g., changing "a|a" to "b|b"), this list should ideally immediately update to show the words in the "b|b" group, providing instant feedback on the merge they are about to perform.

### 4. Filtering & Fast Triage

- Include a prominent toggle switch in the header: **"Unreviewed Only"** vs **"Show All"**.
- Default this to "Unreviewed Only".
- An item is "Unreviewed" if `user_edited` is blank.
- When traversing in "Unreviewed" mode, saving an edit (which sets `user_edited = "x"`) means the item will be filtered out on the next refresh/traversal. Ensure the index management handles this smoothly without skipping items.

### 5. Backend Integration

- Implement an API endpoint (e.g., `/api/curated/root-ids`) to handle POST requests.
- The endpoint reads `/curated/root_ids.csv`, finds the row by `corpus_id`, updates the `root_id` field, sets `user_edited` to `"x"`, and rewrites the file.
