---
id: doc-12
title: Tone Analysis Specification
type: specification
created_date: '2026-06-10 16:29'
---

# Tone Analysis Specification (MVP Stage)

This document specifies the tone analysis module of the dictionary pipeline. The implementation is currently at an **MVP (Minimum Viable Product)** stage, which focuses on a subset of eligible verbs to validate the H1/H2 inference rules.

At the end of the morphology analysis, which yields segmented and tagged verbs, we examine the tone sequences on verbs. The input for this process is the lists of `segmented_forms` found in `reconstructable_verbs.json`.

## Domain Restrictions (MVP Scope)

Currently, the analysis is limited to verbs matching the following criteria:
- **No prepronominal prefixes** (e.g. translocutive, partitive, distributive)
- **No middle voice**
- **No animate object-pronouns**
- **Root does not start with the vowel 'a'** (specifically roots beginning with the vowel 'a', not all vowel-initial roots)

For these verbs, we only analyze the stem (specifically the last two morphemes). We do not consider the immediate or infinitive stems in this stage.

## Tonal Phenomena

### H2: Final Mora High
Makes the last mora of the stem high. H2 can be on any or no forms of a verb.

### H1: High Tones from Glottal Stops
This system deduces the historical position of glottal stops in the verb by using tables of surface tones and the underlying forms they imply. The goal is to infer the complete underlying form (no tones, only glottal placement) and verify that it correctly reconstructs the tones of the surface forms.

Tone orthography concepts are based on `dictionary_pipeline/tone/`, using numeric notation (1-4) where existing mappings apply (e.g., acute=3, grave=2, etc.).

## Constraint Definitions

- **SPREAD**: Spreading happens when there is no local high tone and the preceding syllable is long.
- **NO_SPREAD**: Spreading is blocked if there is a high tone two syllables before the current syllable.
- **BLOCKED**: High tones are blocked if the preceding syllable is already high.

## H1 Inference Table

| Vowel Length | Glottal Class | Environment | Surface Form     |
| :----------- | :------------ | :---------- | ---------------- |
| Long         | PRE_C         | SPREAD      | 23-VV32          |
| Long         | PRE_C         | NO_SPREAD   | VV33             |
| Long         | PRE_C         | BLOCKED     | VV21             |
| Short        | PRE_C         | SPREAD      | 23-VV32          |
| Short        | PRE_C         | NO_SPREAD   | VV32             |
| Short        | PRE_C         | BLOCKED     | VV21             |
| Long         | NO_C          | SPREAD      | VV33' or 23-VV3' |
| Long         | NO_C          | NO_SPREAD   | VV33'            |
| Long         | NO_C          | BLOCKED     | VV2'             |
| Short        | NO_C          | SPREAD      | 23-VV3'          |
| Short        | NO_C          | NO_SPREAD   | VV3'             |
| Short        | NO_C          | BLOCKED     | VV2'             |
| Long         | POST_C        | SPREAD      | VV33             |
| Long         | POST_C        | NO_SPREAD   | VV33             |
| Long         | POST_C        | BLOCKED     | VV22             |
| Short        | POST_C        | SPREAD      | 23-VV3           |
| Short        | POST_C        | NO_SPREAD   | VV3              |
| Short        | POST_C        | BLOCKED     | VV2              |
