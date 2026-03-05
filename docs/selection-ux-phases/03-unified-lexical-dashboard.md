# Phase: The Unified Lexical Dashboard

## Objective

Provide full context for a single word (`corpus_id`) by displaying its available derivation selections, root ID overrides, and suffix connections on one unified screen. This contextual view aids in complex data-entry decisions by presenting all linked metrics for a lemma simultaneously.

## Background

The user frequently references multiple pieces of data to make a single decision:

- Which canonical reconstruction is correct? (`SelectRootsWorkflow`)
- What `root_id` should encompass this corpus ID? (`root_ids.csv`)
- What derivational connections exist for this word? (`derivational_suffix_connections.csv`)

By bringing these three editable state streams into a single route or extended view, the reviewer minimizes context switching.

## Features & Requirements

### 1. Integration or New Route

- **Option A:** Extend the existing `SelectRootsWorkflow` (`/src/components/SelectRootsWorkflow.tsx`). Add a new "Lexical Metadata" panel directly below the main comparison table.
- **Option B (Preferred):** Create a new `/lexical-review/[corpus_id]` route that displays the selected and available root derivations as a "Hero" section, and renders the Root/Suffix components below. This ensures the primary verb-selection UI remains lightweight while providing a deep-dive contextual page per word.

### 2. Root Assignment Component

- Within the panel, identify the current `root_id` for the focused corpus item.
- Render a text input showing that `root_id`.
- Support inline editing (hitting `Enter` saves the new `root_id`).
- **Contextual Search:** If the user types a new `root_id`, immediately display a list of all _other corpus IDs_ in the dataset currently assigned to that new `root_id`. This prevents creating orphan groups or merging into the wrong group blindly.

### 3. Derivations Component

- List any rows from `derivational_suffix_connections.csv` where the focused `corpus_id` appears in either `from_corpus_ids` or `to_corpus_ids`.
- The display should be compact (e.g., small pills or a condensed list) indicating the directional relationship ("Derived From: [Root X]" or "Derived Into: [Root Y]").
- Include a quick toggle/checkbox next to each connection for `user_approved`.
- Note: This component does not support creating net-new manual connections, only rendering and approving proposed heuristics.

### 4. Shared API Layer

- Utilize the same `/api/curated/*` Next.js routes defined in phase 1 and 2 specifications.
- Ensure optimistically updating the UI state when a `root_id` or derivation approval is toggled to match the fast, keyboard-driven pace of the existing dictionary tools.
