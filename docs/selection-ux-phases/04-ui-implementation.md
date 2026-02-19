# Task 4: Interactive Selection UI

## Description

Build the ergonomic user interface for iterating through lexical verbs and selecting derivations. The selected derivation will be featured prominently, with alternative derivations compared against it in a horizontal tabular format.

## Steps

1.  **Create `root-based-dict/src/components/SelectRootsWorkflow.tsx`**:
    - State: `currentIndex` (pointer into the unique corpus IDs) and `selectedDerivationId` (currently focused choice).
    - UI: Display the definition, corpus ID, and a progress indicator (e.g., "15 / 600").
    - Layout:
      - Place the selected derivation in the center (or primary column).
      - Display alternative derivations alongside it horizontally in a tabular view (one column per derivation).
      - Ensure comparable information (configuration flags, roots, etc.) alines on the same row.
    - Information Display (for the selected derivation):
      - All prefix configuration flags
      - Middle voice configuration
      - H and glottal grade roots
      - Class and subvariant
    - Diff Highlighting (for non-selected derivations):
      - Calculate visual diffs against the selected derivation.
      - Highlight the specific tabular cells that differ from the selected derivation's values.
      - Highlight the entire column of the pipeline-selected form in a distinct color when it differs from the user-selected form.
    - Behavior:
      - The default selected derivation is the user-selected form if it exists; otherwise, the pipeline-selected form.
    - Keyboard Shortcuts:
      - `j`/`k` (or Arrow Keys) to change the currently focused/selected derivation column.
      - `Enter` to confirm selection and advance to the next lexical verb/word.
2.  **Visual Polish**:
    - Use clear color coding for diffs and the pipeline's choice.
    - Ensure the horizontal layout handles overflow gracefully (if many derivations exist).
3.  **Verification**:
    - Perform a manual "tagging run" of 5-10 verbs to ensure the UX feels snappy, diffs are easy to read, and errors are minimized.
