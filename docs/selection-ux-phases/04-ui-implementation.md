# Task 4: Interactive Selection UI

## Description

Build the ergonomic user interface for iterating through lexical verbs and selecting derivations.

## Steps

1.  **Create `root-based-dict/src/components/SelectRootsWorkflow.tsx`**:
    - State: `currentIndex` (pointer into the unique corpus IDs).
    - UI: Display the definition, corpus ID, and a progress indicator (e.g., "15 / 600").
    - Table/List: Show all rows for the current `corpus_id`.
    - Features:
      - Highlight the row where `pipeline_selected == 'x'`.
      - Highlight the row where `user_selected == 'x'`.
      - Visualize `segmented_forms` (perhaps a grid of the 5 forms).
      - visualize "flags/features" (stative, class, prefixes, etc.).
    - Keyboard Shortcuts:
      - `j`/`k` or Arrow Keys to change current row selection.
      - `Enter` or `x` to mark the current row as `user_selected`.
      - `h`/`l` or Left/Right Arrows to navigate between lexical verbs.
2.  **Visual Polish**:
    - Use clear color coding for pipeline vs. user selection.
    - Ensure the layout is clean for high-volume work.
3.  **Verification**:
    - Perform a manual "tagging run" of 5-10 verbs to ensure the UX feels snappy and errors are minimized.
