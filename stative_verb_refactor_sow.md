# Statement of Work: Stative Verb Refactor

## Background & Problem Statement

Currently, stative verbs are forced into the same 5-aspect mold as "eventful" verbs during dictionary parsing. However, stative verbs structurally only possess two aspects: **present** and **non-present (incompletive)**.

- **Infinitives:** The "infinitives" listed for stative verbs are actually borrowed forms from another aspect class.
- **Imperatives:** The dictionary imperative column for stative verbs contains either:
  1.  The non-present (incompletive) stem followed by the modal suffix `-esti`.
  2.  The immediate form of a different aspect class.

**The `-esti` Problem:** The pipeline currently attempts to strip modal suffixes when parsing dictionary forms. However, we cannot safely strip `-esti` globally from imperatives, because for some eventful verbs, `-esti` (or `-esdi`) is a genuine part of their immediate aspect ending. The current workaround is injecting `-esdi` directly into the aspect ending tables, which pollutes the pure morphophonological data with modal suffixes.

## Proposed Architecture

We will leverage the new `WordSpec` system to create an Anti-Corruption Layer between the dictionary columns and the morphological engine.

1.  **Pure Aspect Tables:** Do NOT create a separate aspect ending table for stative verbs. The aspect ending tables should remain strictly morphophonological (representing the standard 5 aspects).
2.  **WordSpec as the Translator:** `WordSpec` will instruct the parser and generator on how to handle stative forms. For example, when processing a stative imperative, the `WordSpec` will explicitly indicate that it maps to the `incompletive` aspect and that the `-esti` suffix is involved.

## Implementation Strategy: RowSpec Overgeneration

To cleanly separate the stative and eventful paradigms without complicating the morphological engine's inner loops, we will rely on explicit overgeneration of `row_spec` hypotheses during corpus creation, followed by data splitting during aspect matching.

**1. Dictionary Parsing & Overgeneration (`preprocess_ced`):**

- Add a `row_spec` enum column with values: `pure_stative`, `mixed_inf_only`, `mixed_imp_inf`, `eventful`.
- When parsing a dictionary entry, overgenerate rows for all theoretically possible `row_specs` based on the available data. For example, if both imperative and infinitive are missing, only generate `pure_stative` and `eventful` hypotheses.

**2. Aspect Matching (`identify_aspect_classes`):**

- **Helper Refactoring:** Update the aspect class matcher to accept tuples of `(Aspect, form_string)`. This allows flexibility, such as passing multiple dictionary columns mapped to `Aspect.INCOMPLETIVE`.
- **Data Splitting:** When evaluating a mixed `row_spec`, regroup the forms into a Stative subset and an Eventful subset based on the specification.
- **Independent Matching:** Run the matcher independently on the Stative forms (generating stative aspect candidates) and the Eventful forms (generating eventful aspect candidates).
- **Row Bifurcation:** A single mixed row entering this phase will be saved to disk as multiple rows leaving it: stative rows (containing only forms assigned to the stative class) and eventful rows (containing only forms assigned to the eventful class).

**3. Prefix Derivation (`identify_prefixes`):**

- Because the data was fully split in the previous phase, the pronoun matching logic simply operates on whatever forms are present in the row. It does not need to know the complex relationship between the rows.

**4. Canonical Selection (`select_canonical_derivations`):**

- When grouping derivations by `corpus_id` for user selection, the interface must prompt the user to first select the correct canonical `row_spec`.
- If a mixed `row_spec` is selected, the interface must allow the user to select _both_ the canonical stative derivation and the canonical eventful derivation.

## Next Steps for the Next Agent (Phase 1: Pure Refactors)

To begin this implementation safely without breaking current program output, the first agent should focus on these "pure" refactors:

1. **Introduce `Scope` Enum and `FormSpec` Abstraction:**
   - **`Scope`:** Define the `Scope` enum in the core models. A `Scope` tells us _which fields_ of the corpus row the analysis is trying to account for. Values: `STATIVE_WITH_IMP`, `STATIVE_NO_IMP`, `EVENTFUL`, `EVENTFUL_INF_ONLY`, `EVENTFUL_IMP_INF`. Update the aspect class indentification phase to assume _every_ row is `Scope.EVENTFUL` and add `scope` to each CSV artifact saved to disk. Simply pass along this value unchanged, like you would `corpus_id`.
   - **`FormSpec` (Currying `WordSpec`):** Create an intermediate object `FormSpec` containing `aspect: Aspect`, `person: str`, `allow_set_a: bool`, and `stative: bool` (which will eventually be dropped). This prevents requiring a `PronominalConfig` too early. Create a function `(Scope, form) -> FormSpec` which throws an unimplemented error if `Scope` is not `eventful`.
   - **Downstream Operations & Mapping:** The mapping will become `(Scope, form_name) -> FormSpec` early in the pipeline, and later `(FormSpec, PronominalConfig) -> WordSpec`. Update `calculate_set_name` and `build_wordspec` to use this new curried approach. For now, the `(Scope, form_name) -> FormSpec` scaffolding functions should throw `NotImplementedError` for any value other than `Scope.EVENTFUL`. This lays the structural groundwork without changing behavior and acts as a tripwire for future work.
2. **Refactor Aspect Class System:**
   - Create a new function inside the aspect class system (morphological engine) that operates on `(Aspect, form_string, allow_h_alternation)` tuples.
   - Update `identify_aspect_classes` to construct this list of tuples dynamically based on the row's `RowSpec` value, and pass it to the new function.
   - This cleanly removes the current bad design where dictionary "form names" leak into the `get_candidates_combined` function.
   - Write unit tests passing in multiple entries with the _same_ `Aspect` (e.g., testing the system's ability to handle multiple `Aspect.INCOMPLETIVE` forms for statives, even if the current pipeline doesn't use that feature yet).
3. **Robust Prefix Identification:** Update `identify_prefixes` to be fully robust to missing form data (since future split rows will omit forms like infinitive or imperative). Add unit tests proving that it correctly skips and processes rows with dropped forms without crashing.
