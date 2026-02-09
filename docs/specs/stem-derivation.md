# Stem Derivation Specification

## Objective

Stem derivation is the process of extracting the underlying morphological stem(s) from a set of surface forms. The goal is to separate the "guessing" of morphological structure from the "validation" of that structure against surface forms, making the logic explicit, consistent, and serializable.

## Motivation

- **Explicit Decisions**: Record _why_ a stem was derived (e.g., "This verb uses the `ka-` variant of 3rd person Set A").
- **Strict Consistency**: A chosen configuration must validly explain _all_ provided forms.
- **Separation of Concerns**: Pre-pronominal prefixes (T, P, D) and Pronominal prefixes operate at different layers.

## Architecture

### 1. Configuration Objects

The configuration is split into two layers:

#### A. `PrePronominalConfig`

Handles the outer prefixes: Translocutive, Partitive, Distributive.

```python
@dataclass(frozen=True)
class PrePronominalConfig:
    translocutive: bool = False
    translocutiveImpOnly: bool = False
    partitive: bool = False
    distributive: bool = False
    distributiveImpIsFutProg: bool = False
```

#### B. `PronominalConfig`

Handles the inner pronominal inflection and stem properties.

```python
@dataclass(frozen=True)
class PronominalConfig:
    set_type: str  # 'a' | 'b'
    stem_type: StemType
    metathesis_strategy: MetathesisStrategy = MetathesisStrategy.NONE
    use_ka_variant: bool = False
    use_uwa_for_3rd_set_b: bool = False
    use_aki_for_1st_set_b: bool = False
    use_3rd_person_object: bool = False
```

### 2. Enums

#### `StemType`

- `CONSONANT` ("con")
- `VOWEL_A` ("vowel_a")
- `VOWEL_E` ("vowel_e")
- `VOWEL_O` ("vowel_o")
- `VOWEL_U` ("vowel_u")
- `VOWEL_V` ("vowel_v")
- `VOWEL_I` ("vowel_i")
- `ASPIRATED` ("aspirated")
- `S_STEM` ("s_stem")

#### `MetathesisStrategy`

- `NONE` ("none")
- `H_CONS` ("h_cons")
- `VOWEL` ("vowel")

### 3. The `Derivation` Result Object

The `Derivation` object represents a _successful_ application of a configuration to a set of forms.

```python
@dataclass
class Derivation:
    pre_config: PrePronominalConfig
    pron_config: PronominalConfig
    consensus_stem: str
    stems: Dict[str, str]
    metathesis_involved: bool = False
```

## Derivation Logic

### 1. Strip Pre-pronominals

`strip_prepronominals(forms, pre_config) -> Optional[Dict[str, str]]`

- Attempts to strip the Translocutive/Partitive/Distributive prefixes defined in `pre_config` from all forms.
- Returns the `intermediate_forms` (pronominal bases) if successful.

### 2. Derive Pronominals

`derive_pronominals(intermediate_forms, pron_config) -> Optional[Derivation]`

- Takes the clean `intermediate_forms`.
- Applies the `pron_config` logic (lookup prefix -> strip -> reverse metathesis).
- Validates consistency via `stems_are_consistent`.

### 3. Derive Middle Voice

`derive_middle(der) -> List[Derivation]`

- Takes a successful pronominal derivation.
- Checks if the derived root matches known middle voice patterns (e.g., `ali-`, `ati-`, `at(at)-`).
- If a match is found, creates _additional_ derivations for the underlying root (stripping the middle voice prefix).
- Returns the original derivation plus any middle-voice derived options.

### 4. Consistency Validation

`stems_are_consistent(derived_stems, pron_config) -> Optional[str]`

- Ensures that all derived stems are consistent with each other.
- **h-grade**: The standard Consensus Stem, derived from 3rd person forms.
- **glottal-grade**: The stem used for 1st person and specific other configurations (e.g., 2->3).
- Checks compatibility between h-grade and glottal-grade candidates using `grades_are_compatible`.

## Guessing Strategy (The Outer Loop)

The `StemDeriver.derive_row` method implements a nested loop to find valid configurations:

1.  Iterate all valid `PrePronominalConfig` combinations.
2.  For each valid pre-config, iterate `PronominalConfig` candidates:
    - Determine `set_type` (a/b) based on the "present" form.
    - Test `use_3rd_person_object` (True/False).
    - Test all `MetathesisStrategy` options.
    - Test all `StemType` options.
    - Auto-detect `use_ka_variant`, `use_aki_for_1st_set_b`, and `use_uwa_for_3rd_set_b`.
3.  Collect and rank successful `Derivation` objects.

## Dual Grade Handling

The system utilizes h-grade and glottal-grade stems:

- **h-grade**: Derived from 3rd person forms.
- **glottal-grade**: Derived from "1st to 3rd" or "1st Set A" forms.
- The reconstruction engine selects between these grades based on the `PronominalConfig`.

### Imperative Consistency Allowance

To support verbs where the imperative form (2->3) reflects the glottal grade, the system allows the `imperative` form to diverge from the consensus stem when `use_3rd_person_object` is enabled.
