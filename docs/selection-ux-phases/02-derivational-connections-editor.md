# Phase: Derivational Connections Editor

## Objective

Create a standalone sequential review interface for approving heuristic-generated derivational relationships in `curated/derivational_suffix_connections.csv`.

## Background

The `derivational_suffix_connections.csv` file is an auto-generated list of potential connections between a "base" root and a "derived" root. Humans review these proposals and mark valid ones by setting `user_approved = "x"`. Creating brand new manual connections is not supported or required from the UI; the focus is solely on triaging the pipeline proposals.

## Features & Requirements

### 1. Route & Layout

- Create a new Next.js route: `/review-derivations`.
- Provide a header for navigation:
  - Total connections progress (e.g., `12 / 105 connections reviewed`).
  - Next/Prev arrow buttons (with `Left`/`Right` arrow keyboard shortcuts).

### 2. The Data Display

The UI must clearly present the two sides of the connection to facilitate a fast yes/no decision.

- **Left Column ("From"):**
  - Display `from_root_id`, `from_h_grade`, `from_g_grade`, `from_class`, and `from_stem_type`.
  - Also fetch and display the English definitions mapped to the `from_corpus_ids` so the user knows what words these represent.
- **Right Column ("To"):**
  - Display `to_root_id`, `to_h_grade`, `to_g_grade`, `to_class`, and `to_stem_type`.
  - Fetch and display the English definitions for `to_corpus_ids`.
- **Highlighting Differences:** Visually highlight the fields that differ between the left and right sides (e.g., if the `from_class` is "active" and the `to_class` is "cause", highlight "cause").

### 3. Primary Action

- A prominent checkbox, toggle switch, or large button to mark the connection as **Approved**.
- Hitting `Enter` should toggle the approval state and automatically advance to the next connection.

### 4. Filtering & Fast Triage

- Include a toggle switch in the header: **"Unreviewed Only"** vs **"Show All"**.
- Default to "Unreviewed Only".
- An item is Unreviewed if `user_approved` is blank.

### 5. Backend Integration

- Implement an API endpoint (e.g., `/api/curated/derivational-connections`) to handle POST requests.
- The endpoint must match the connection using the unique composite key (the 8-tuple of from/to root and class data).
- The endpoint toggles `user_approved` and rewrites `/curated/derivational_suffix_connections.csv`.
- Ensure sorting or row order is relatively stable when rewriting, matching the Python pipeline's sorting logic if possible.
