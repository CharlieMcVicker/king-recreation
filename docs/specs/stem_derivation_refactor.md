# Stem Derivation Refactoring Plan

## Objective

Refactor the stem derivation logic in `derive_stems.py` to use a **configuration-driven** approach. This will separate the "guessing" of morphological structure from the "validation" of that structure against surface forms, making the logic explicit, consistent, and serializable.

## Motivation

- **Explicit Decisions**: We want to record _why_ a stem was derived (e.g., "This verb uses the `ka-` variant of 3rd person Set A").
- **Strict Consistency**: A chosen configuration (e.g., "Vowel Stem") must validly explain _all_ provided forms.
- **Separation of Concerns**: Pre-pronominal prefixes (T, P, D) and Pronominal prefixes operate at different layers. Splitting them simplifies the combinatorial logic.

## Proposed Architecture

### 1. Configuration Objects

We split the configuration into two layers:

#### A. `PrePronominalConfig`

Handles the outer prefixes: Translocutive, Partitive, Distributive.

```python
@dataclass(frozen=True)
class PrePronominalConfig:
    translocutive: bool
    partitive: bool
    distributive: bool
```

#### B. `PronominalConfig`

Handles the inner pronominal inflection and stem properties.

```python
@dataclass(frozen=True)
class PronominalConfig:
    set_type: str  # 'Set A' | 'Set B'

    # Stem / Root Properties
    stem_type: StemType  # Enum: CONSONANT, VOWEL, VOWEL_AE, ...

    # Metathesis Strategy
    metathesis_strategy: MetathesisStrategy  # Enum: NONE, H_CONS, VOWEL_METATHESIS

    # 3rd Person Set A Variant Flag
    # If True: Expect 'ka-' (before cons) / 'k-' (before vowel)
    # If False: Expect 'a-' (before cons/-a) / 'ø-' (before other vowels)
    use_ka_variant: bool
```

### 2. The `Derivation` Result Object

The `Derivation` object represents a _successful_ application of a configuration to a set of forms.
It **composes** the configuration objects rather than duplicating them.

```python
@dataclass
class Derivation:
    # The accepted configurations
    pre_config: PrePronominalConfig
    pron_config: PronominalConfig

    # The resulting Single Root (if reachable) or Consensus Stem
    root: str

    # The specific stems used for each form (for transparency)
    forms_stem_usage: Dict[str, str]
```

### 3. Derivation Logic (Decoupled System)

We define two distinct operations:

#### A. `strip_prepronominals(forms, pre_config) -> Optional[Dict[str, str]]`

- Attempts to strip the Translocutive/Partitive/Distributive prefixes defined in `pre_config` from all forms.
- Returns the `intermediate_forms` (pronominal bases) if successful.
- Returns `None` if any form differs from the expected prefix pattern.

#### B. `derive_pronominals(intermediate_forms, pron_config) -> Optional[Derivation]`

- Takes the clean `intermediate_forms`.
- Applies the `pron_config` logic (lookup prefix -> strip -> reverse metathesis).
- Validates consistency of the resulting stems.
- Returns a `Derivation` object (composing both configs) if successful.

### 4. Guessing Strategy (The Outer Loop)

We maximize efficiency by filtering invalid outer layers first.

1.  **Find Valid Pre-Configs**:
    - Iterate all 8 `PrePronominalConfig` combinations.
    - Run `strip_prepronominals(forms, config)`.
    - Keep only the successful `(config, intermediate_forms)` pairs.
2.  **Iterate Pronominal Configs**:
    - For each valid `intermediate_forms` set:
      - Iterate `PronominalConfig` candidates (Set/StemType/Flags).
      - Run `derive_pronominals`.
3.  **Collect & Rank**:
    - Collect all successful `Derivation` objects.
    - Rank if necessary.

## Implementation Details

### `king_recreation/phonology_data.py`

- Add `StemType` Enum.
- Add `MetathesisStrategy` Enum.
- Implement Prefix Lookup Table: `(Set, StemType, UseKa) -> Prefix`.

### `king_recreation/derive_stems.py`

- Separate `strip_prepronominals` logic.
- Separate `strip_pronominals` logic.
- Implement the nested guessing loop.

### Verification

- Regress entire corpus.
- **Critical Check**: If `stem_corpus.csv` changes significantly (rows failing that used to pass, or massive changes in stem shapes), HALT and investigate.
- Manual verification of new columns in `stem_corpus.csv`.
