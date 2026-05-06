# Implementation Plan: Stative Verb Refactor (Phase 1)

This plan outlines the "pure refactor" phase to introduce the `Scope` and `FormSpec` abstractions. These changes decouple dictionary column concepts from the morphological engine and lay the groundwork for stative verb support.

## Core Models & Types

### [MODIFY] [morphology_types.py](file:///Users/charlesmcvicker/code/king-recreation/king_recreation/morphology_types.py)
- **Introduce `Scope` Enum:**
  - Values: `STATIVE_WITH_IMP`, `STATIVE_NO_IMP`, `EVENTFUL`, `EVENTFUL_INF_ONLY`, `EVENTFUL_IMP_INF`.
  - This enum tells the pipeline which fields of the corpus row the current analysis is accounting for.

### [MODIFY] [word_spec.py](file:///Users/charlesmcvicker/code/king-recreation/king_recreation/word_spec.py)
- **Define `FormSpec` Dataclass:**
  ```python
  @dataclass(frozen=True)
  class FormSpec:
      aspect: Aspect
      person: str
      allow_set_a: bool
      stative: bool
  ```
- **Refactor `calculate_set_name`:**
  - New signature: `calculate_set_name(spec: FormSpec, config: PronominalConfig) -> Optional[str]`
  - Simplified logic: `target_set_is_a = verb_is_set_a and spec.allow_set_a`.
  - This removes the hard-coded `Aspect.PERFECTIVE`/`Aspect.INFINITIVE` checks from the core pronoun logic.

## Dictionary Bridge

### [MODIFY] [dictionary_forms.py](file:///Users/charlesmcvicker/code/king-recreation/king_recreation/dictionary_forms.py)
- **Implement `get_form_spec(scope: Scope, form_name: str) -> FormSpec`:**
  - Acts as the translator between a dictionary column and its structural requirements.
  - For `Scope.EVENTFUL`, use existing `FORM_NAME_TO_ASPECT` and `FORM_NAME_TO_PERSON`.
  - Set `allow_set_a` to `False` for `PERFECTIVE` and `INFINITIVE`, and `True` for others (maintaining current behavior).
  - Throw `NotImplementedError` for non-`EVENTFUL` scopes for now.
- **Update `build_wordspec`:**
  - New signature: `build_wordspec(form_spec: FormSpec, config: PronominalConfig) -> WordSpec`
  - It now receives a pre-calculated `FormSpec` and "enriches" it with the verb's lexical config.

## Pipeline & Artifact Persistence

### [MODIFY] [artifacts.py](file:///Users/charlesmcvicker/code/king-recreation/king_recreation/phases/identify_aspect_classes/artifacts.py)
- Update `StrippedVerbRow` to include a `scope` field (defaulting to `"EVENTFUL"`).
- Update `dict_keys` to ensure `scope` is written to `corpus_no_asp.csv`.

### [MODIFY] [artifacts.py](file:///Users/charlesmcvicker/code/king-recreation/king_recreation/phases/identify_prefixes/artifacts.py)
- Ensure `save_stripped_roots` preserves the `scope` column when writing to `corpus_no_pre_no_asp.csv`.

### [MODIFY] [artifacts.py](file:///Users/charlesmcvicker/code/king-recreation/king_recreation/phases/identify_derived_verbs/artifacts.py)
- Update `save_derivational_connections` to include the `scope` field in the output CSV.

### [MODIFY] [identify_aspect_classes/__init__.py](file:///Users/charlesmcvicker/code/king-recreation/king_recreation/phases/identify_aspect_classes/__init__.py)
- Update the main loop to assign `Scope.EVENTFUL` to all rows.
- Ensure the value is passed through to the artifact saving logic.

## Verification Plan

### Automated Tests
- `tests/test_dictionary_bridge.py`: Verify `get_form_spec` returns correct `FormSpec` for all `EVENTFUL` forms.
- `tests/test_pronoun_routing.py`: Verify `calculate_set_name` correctly handles `allow_set_a` toggle.

### Manual Verification
- Run the full pipeline and verify that `artifacts/corpora/*.csv` files now contain a `scope` column populated with `EVENTFUL`.
