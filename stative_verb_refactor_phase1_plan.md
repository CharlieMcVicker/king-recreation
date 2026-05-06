# Implementation Plan: Stative Verb Refactor

This plan outlines the staged approach to support stative verb morphology. We have completed the structural foundation by overhauled the pronominal system. Future phases will focus on making the pipeline "scope-aware".

## Phase 1: Pronominal System Overhaul [COMPLETED]

The pronominal system has been migrated from magic strings to type-safe Enums. **Do not introduce string-based "set_names" in new code.**

### 1. Structural Types (`king_recreation/morphology_types.py`)
- **Implemented Enums:** `Person`, `Number`, `PronominalSet`.
- **Note:** Always use these Enums for morphological specification.

### 2. Specification Models (`king_recreation/word_spec.py`)
- **`FormSpec`**: Captures abstract requirements for a form (Aspect, Person, Stative-ness).
- **`WordSpec`**: Fully resolved morphological key.
- **`calculate_pronominal_key`**: Core routing logic that maps features to a `(Person, Number, PronominalSet)` tuple.

### 3. Dictionary Bridge (`king_recreation/dictionary_forms.py`)
- **`get_form_spec(form_name: str) -> FormSpec`**: Central map between dictionary columns and their requirements.
- **`build_wordspec(form_name: str, config: PronominalConfig, stative: bool) -> WordSpec`**: Final resolution of a word's morphology.

### 4. Pronominal Engine (`king_recreation/morphemes/prefixes/pronominals.py`)
- **`PronominalConfig`**: Now uses `PronominalSet` Enum.
- **Mapping Lookup**: String-based `if/else` chains replaced with structured Enum lookups.

---

## Phase 2: Scope-Aware Pipeline [FUTURE WORK]

The goal of this phase is to allow the pipeline to handle different "scopes" (e.g., Eventful vs. Stative) which dictate which dictionary forms are available and how they map to morphology.

### 1. Define `Scope` Enum (`king_recreation/morphology_types.py`)
- Values: `STATIVE_WITH_IMP`, `STATIVE_NO_IMP`, `EVENTFUL`, `EVENTFUL_INF_ONLY`, `EVENTFUL_IMP_INF`.
- This enum tells the pipeline which fields of the corpus row the current analysis is accounting for.

### 2. Update `get_form_spec` Signature
- **New Signature:** `get_form_spec(scope: Scope, form_name: str) -> FormSpec`
- **Logic:**
  - For `Scope.EVENTFUL`, maintain current mappings.
  - For `Scope.STATIVE_*`, implement the 2-aspect mapping (Present/Incompletive).
  - Throw `NotImplementedError` for unsupported Scope/Form combinations.

### 3. Pipeline & Artifact Persistence
- **Identify Aspect Classes**: Assign a `Scope` to each verb row (initially defaulting to `EVENTFUL`).
- **Artifacts**: Add a `scope` column to:
  - `corpus_no_asp.csv`
  - `corpus_no_pre_no_asp.csv`
  - `reconstructable_verbs.json`
- This ensures that downstream phases (Prefix identification, Reconstruction) know which morphological rules to apply.

### 4. Verification
- Verify that `EVENTFUL` rows continue to reconstruct perfectly.
- Add tripwire tests for `Scope.STATIVE` that expect `NotImplementedError`.

## Design Principles
1. **No Magic Strings**: All morphological lookups must use Enums or Enum-tuples.
2. **Scoping Early**: The `Scope` should be identified as early as possible in the pipeline (Dictionary ingest) and persisted through all artifacts.
3. **Pure Refactor First**: Ensure the new `Scope` architecture works for `EVENTFUL` verbs before implementing the actual stative logic.
