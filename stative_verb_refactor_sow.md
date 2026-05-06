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

## Completed Work: Pronominal System Overhaul (Phase 1)

The first phase of the refactor is complete. The pronominal system has been migrated from magic strings to a type-safe Enum system.

1. **Enum Migration:** `Person`, `Number`, and `PronominalSet` Enums have been implemented.
2. **WordSpec & FormSpec:** The core specification models now use these Enums. `calculate_pronominal_key` handles the routing logic structurally.
3. **Dictionary Bridge:** A centralized bridge exists in `dictionary_forms.py` to map dictionary columns to their morphological requirements via `FormSpec`.
4. **Engine Updates:** All morphological engines (prefix derivation, reconstruction) have been updated to use the new Enum-based specifying API.

---

## Next Steps: Scope-Aware Pipeline

The next phase focuses on implementing the `Scope` architecture to support distinct stative verb mappings.

1. **Introduce `Scope` Enum and Artifact Persistence:**
   - Define the `Scope` enum in `morphology_types.py`. Values: `STATIVE_WITH_IMP`, `STATIVE_NO_IMP`, `EVENTFUL`, `EVENTFUL_INF_ONLY`, `EVENTFUL_IMP_INF`.
   - Update `identify_aspect_classes` phase to assign `Scope.EVENTFUL` to all rows and propagate this field through all CSV artifacts (`corpus_no_asp.csv`, `corpus_no_pre_no_asp.csv`, etc.).
2. **Make `get_form_spec` Scope-Aware:**
   - Update `get_form_spec(scope: Scope, form_name: str) -> FormSpec` in `dictionary_forms.py`.
   - Implement the mapping logic for stative scopes (e.g., mapping both "incompletive" and "imperative" to `Aspect.INCOMPLETIVE` for statives).
3. **Refactor Aspect Class System:**
   - Create a new function inside the aspect class system (morphological engine) that operates on `(Aspect, form_string, allow_h_alternation)` tuples.
   - This removes the dependency on dictionary "form names" within the core morphological matching logic.
4. **Robust Prefix Identification:** 
   - Ensure `identify_prefixes` is fully robust to missing form data (since future split rows will omit forms like infinitive or imperative).
   - Add unit tests proving that it correctly skips and processes rows with dropped forms without crashing.
