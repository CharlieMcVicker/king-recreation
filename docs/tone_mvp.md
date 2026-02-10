we are going to plan a new module of analysis. at the end of our current analysis which leaves us with segmented tagged verbs, we are going to examine the tone sequences on verbs. The input for this process is the lists of "segmented_forms" found in `reconstructable_verbs.json`.

we will consider for now, only verbs with:

no prepronominal prefixes
no middle voice
that do not have a root starting with -a (specifically roots beginning with the vowel 'a', not all vowel-initial roots)

these will be easier to begin with. we will only analyze the stem (limit of domain is the last two morphemes). we will not consider the immediate or infinitive stems yet.

we will consider two tonal phenomena. one, called

h2, or "final_mora_high" makes the last mora of the stem high. h2 can be on any or no forms of a verb.

h1, or "high tones from glottal stops" will be a bigger task. we will deduce the historical position of glottal stops in the verb by using tables of surface tones and the underlying forms they imply.

Tone orthography concepts are based on `king_recreation/check_tone_consistency.py`, using numeric notation (1-4) where existing mappings apply (e.g., acute=3, grave=2, etc.).

### Constraint Definitions

- **SPREAD**: Spreading happens when there is no local high tone and the preceeding syllable is long.
- **NO_SPREAD**: Spreading is blocked if there is a high tone two syllables before the current syllable.
- **BLOCKED**: High tones are blocked if the preceeding syllable is already high.

### Inference Table

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

for the h1 system, we will try to infer the complete underlying form (no tones, only glottal placement). we will test that this reconstructs the tones of the surface forms.
