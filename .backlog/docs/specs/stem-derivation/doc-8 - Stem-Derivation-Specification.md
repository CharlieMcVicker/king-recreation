---
id: doc-8
title: Stem Derivation Specification
type: specification
created_date: '2026-06-10 16:18'
updated_date: '2026-06-10 16:18'
---# Stem Derivation Specification

Stem derivation is the process of extracting the underlying morphological stem(s) from a set of surface forms. The goal is to separate the "guessing" of morphological structure from the "validation" of that structure against surface forms, making the logic explicit, consistent, and serializable.

---

## 1. Motivation

- **Explicit Decisions**: Record *why* a stem was derived (e.g., "This verb uses the `ka-` variant of 3rd person Set A").
- **Strict Consistency**: A chosen configuration must validly explain *all* provided forms.
- **Separation of Concerns**: Pre-pronominal prefixes (T, P, D) and Pronominal prefixes operate at different layers.

---

## 2. Configuration & Structs

Implemented under [morphology/morphemes/prefixes/](../../../../morphology/morphemes/prefixes/):

### A. PrePronominalConfig
Defined in [prepronominals.py](../../../../morphology/morphemes/prefixes/prepronominals.py), handles Translocutive, Partitive, and Distributive outer prefixes.

### B. PronominalConfig
Defined in [pronominals.py](../../../../morphology/morphemes/prefixes/pronominals.py), handles inner pronominal inflection and stem properties (like `set_type`, `stem_type`, `allow_h_metathesis`, `use_ka_variant`, `use_uwa_for_3rd_set_b`, `use_aki_for_1st_set_b`, `use_3rd_person_object`).

### C. PrefixConfig
Unified container defined in [prefixes/__init__.py](../../../../morphology/morphemes/prefixes/__init__.py).

---

## 3. Derivation Logic

The primary derivation steps are orchestrated by the prefix identification pipeline phase in [identify_prefixes/__init__.py](../../../../dictionary_pipeline/phases/identify_prefixes/__init__.py):

1. **Strip Pre-pronominals**:
   - Strip Translocutive/Partitive/Distributive prefixes from all forms to yield intermediate pronominal bases.
2. **Derive Pronominals**:
   - Takes clean intermediate forms, resolves pronominal prefix combinations (by lookup -> strip -> reverse metathesis), and checks consistency.
3. **Derive Middle Voice**:
   - Strips middle voice prefixes (e.g. `ali-`, `ati-`) to find underlying root options (defined in [middle_voice.py](../../../../morphology/morphemes/middle_voice.py)).
4. **Consistency Validation**:
   - Verifies h-grade and glottal-grade compatibility (using `grades_are_compatible`).

---

## 4. Guessing Strategy & Dual Grade Handling

- **Outer Loop**: Iterates through combinations of `PrePronominalConfig` and `PronominalConfig` candidates, collects successfully validated derivations, and ranks them.
- **Dual Grade**: Extracts the `h-grade` stem from 3rd person forms and `glottal-grade` stem from 1st person or transitive forms (2->3, 1->3) to pass to the [Reconstruction Specification](doc-7).
- **Imperative Consistency**: To support verbs where the imperative (2->3) reflects the glottal grade, the system allows the imperative form to diverge from the consensus stem when `use_3rd_person_object` is enabled.
