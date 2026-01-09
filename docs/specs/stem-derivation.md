# Pronouns and stems

To improve our analysis we will derive pronominal-inflection patterns for all our verbs. Our goal will be to label each row of the corpus with:

1. **Inflectional pattern:** two features:
   - Set A vs Set B
   - +/- 2nd to 3rd for imperative
2. **Pre-Pronominal prefixes:** for each prefix:
   - Boolean flag for if it is present - flag only if a prefix occurs on all forms
3. **Present stem:** the present tense form with the pre-pronominal and pronominal prefixes removed. Should have the right stem initial that matches the other forms.

A single form doesn't have enough information to decide exactly all of these features. Make a list of possible derivations based on each form and find the derivation which can explain all forms.

**Selection Rules:**

- For variants like `ø/k-` or `a-/ka-` (3rd Set A) and `u-/uwa-` (3rd Set B) before consonants, **try both**. A verb will use one variant consistently across its stems, but which one is used is a lexical property of the verb.
- **Set B u-**: This variant **always replaces a-** when the stem starts with `a`.

Also flag if multiple explanations of the data are possible for each row.

Lastly, forms where stems could not be derived are saved to `artifacts/reports/stem_derivation_failures.csv`.
Results are saved to `artifacts/data/stem_corpus.csv`.

## Pronominal prefixes

There are two main patterns of person inflection we might see. These are called Set A and Set B verbs.

### Set A pattern

For Set A verbs, we expect to see the following person-prefixes on each form

- Present: 3rd person set A singular
- Present 1sg: 1st person set A singular or 1st person to 3rd person
- Incompletive: 3rd person set A singular
- Completive: 3rd person set B singular
- Imperative: 2nd person set A singular or 2nd person to 3rd person
- Infinitive: 3rd person set B singular

### Set B pattern

For Set B verbs, we expect to see the following person-prefixes on each form

- Present: 3rd person set B singular
- Present 1sg: 1st person set B singular or 1st person to 3rd person
- Incompletive: 3rd person set B singular
- Completive: 3rd person set B singular
- Imperative: 2nd person set B singular or 2nd person to 3rd person
- Infinitive: 3rd person set B singular

### Phonological content of prefixes

| Pronoun           | Form                | Stem initial    |
| ----------------- | ------------------- | --------------- |
| 3rd person Set A  | ø, k-               | a, e            |
| 3rd person Set A  | k-                  | o, u, v         |
| 3rd person Set A  | a-, ka-             | consonants      |
| 3rd person Set A  | kha-                | h + consonant   |
| 3rd person Set A  | kh-                 | V + h           |
| 3rd person Set B  | u- (replaces a)     | a               |
| 3rd person Set B  | uw-                 | e, o, u, v      |
| 3rd person Set B  | uhw-                | V + h           |
| 3rd person Set B  | uwa- (v is dropped) | v               |
| 3rd person Set B  | u-, uwa-            | consonants      |
| 2nd person Set B  | ts-                 | a, e, o, u , v  |
| 2nd person Set B  | tsa-                | consonants      |
| 2nd person Set B  | ts-                 | aspirated cons. |
| 2nd person Set B  | t-                  | s               |
| 2nd person Set A  | h-                  | a, e, o, u , v  |
| 2nd person Set A  | h-                  | V + h           |
| 2nd person Set A  | hi-                 | consonants      |
| 2nd person to 3rd | hiy-                | a, e, o, u , v  |
| 2nd person to 3rd | hi-                 | consonants      |
| 1st person Set A  | k-                  | a, e, o, u, v   |
| 1st person Set A  | tsi-                | consonants      |
| 1st person Set B  | akw-                | a, e, o, u, v   |
| 1st person Set B  | aki-, ak-           | consonants      |
| 1st person Set B  | akh-                | aspirated, s    |
| 1st person Set B  | ak-                 | h               |
| 1st person to 3rd | tsiy-               | a, e, o, u, v   |
| 1st person to 3rd | tsi-                | consonants      |

## Prepronominal prefixes

There are sometimes prefixes before the pronouns that make splitting off the pronouns hard. We will consider three prefixes for now.

### Translocutive

| Stem form | Prefix form                 | Following sound |
| --------- | --------------------------- | --------------- |
| All forms | w-                          | vowels          |
| All forms | hw- (h on right is dropped) | h               |
| All forms | wi-                         | consonants      |

### Partitive

| Stem form   | Prefix form                 | Following sound |
| ----------- | --------------------------- | --------------- |
| Infinitive  | iy-                         | a, e, o, u, v   |
| Infinitive  | i-                          | consonants      |
| Infinitive  | ø                           | -i              |
| Other forms | n-                          | vowels          |
| Other forms | hn- (h on right is dropped) | h               |
| Other forms | ni-                         | consonants      |

### Distributive

| Stem form              | Prefix form       | Following sound |
| ---------------------- | ----------------- | --------------- |
| Infinitive, imperative | t-                | h               |
| Infinitive, imperative | ti-               | consonants      |
| Infinitive, imperative | ts-               | vowels          |
| Other forms            | t-                | a, e, o, u, v   |
| Other forms            | te-               | consonants      |
| Other forms            | te- (replaces -i) | -i              |

## Other considerations

- **Stem Consistency**: All forms for an item in the corpus will have the same stem-initial sound. In addition, all forms with the same pronoun on a given verb will take the same variant. Eg. if a verb takes k- before -e for 3rd person Set A in one form, it will take the g- variant in all forms.
- **/h/ Alternation**: Certain person-prefixes (2nd -> 3rd, 1st -> 3rd, and 1st Set A) cause the first /h/ in a stem (after the pronoun) to turn to a glottal stop (which is dropped). During derivation, if we encounter a stem in one of these contexts that seems to be missing an initial /h/, we should consider the version with /h/ restored as a valid candidate.
- **H-Metathesis**: Sometimes an /h/ in a stem "fuses" with the pronoun prefix.
  - **Type 1 (Consonant)**: /h/ followed by a consonant fuses with a prefix (e.g., `ka-` + `hnoki` -> `khanoki`).
  - **Type 2 (Vowel)**: A stem starting with a vowel+/h/ fuses with a prefix (e.g., `k-` + `ehlatitoh` -> `khelatitoh`, `uw-` + `ehlatitoh` -> `uhwelatitoh`).
  - During stem derivation, the system detects these fusions and restores the underlying /h/ into the stem to ensure consistency across forms.
- **Stem Initial Disambiguation**: The choice of prefix variant (e.g., `a-` before consonant vs `ø` before `a`) is disambiguated by checking other forms of the same verb to ensure a consistent stem-initial sound.
- **Partitive ø**: Before a stem or pronoun starting with `-i`, the Partitive prefix has a null form (`ø`).
- **Distributive de-**: A following `-i` is masked (disappears) when it follows the `te-` variant of the Distributive prefix.
- **Present Stem Extraction**: For each valid derivation that explains all forms, strip the prefixes from the **present tense** form to derive the Present Stem. If multiple derivations are valid, include all resulting stems in a list for that row.
