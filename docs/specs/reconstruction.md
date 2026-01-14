# Reconstruction from Roots Specification

## Consonant Respelling Reform

To simplify the internal representation and phonological rules, the following consonant clusters are respelled during preprocessing:

| Original | Respelled |
| :------- | :-------- |
| `hw`     | `wh`      |
| `hy`     | `yh`      |
| `hl`     | `lh`      |
| `hn`     | `nh`      |

This change ensures that `/h/` always follows the resonant in these clusters, which simplifies prefix attachment and metathesis logic by treating them as standard consonant-starting stems where the aspiration is part of the cluster.

## Proposed Architecture

### 1. Root Extraction & Grade Selection

The process begins by reading `matches.csv` to identify verbs with the **`reconstructs`** scope and fetching their derived stems from `stem_corpus.csv`.

**Logic:**

1.  **Input**: Iterate through verbs flagged as `reconstructs` in `matches.csv`.
2.  **Dual Roots**: The system extracts two roots:
    - **h-grade root**: The unalternated base, used for most forms.
    - **glottal-grade root**: The `/h/`-alternated base (from `present_1sg`).
3.  **Grade Selection**: For each target form, the engine selects the appropriate grade:
    - **Glottal Grade**: Used for `present_1sg` (if Set A or to 3rd) and `imperative` (if to 3rd).
    - **H-Grade**: Used for all other forms.
4.  **Consistency Check**: Verifies that `drop_first_h(h_root) == glottal_root`. Mismatches are flagged but do not necessarily block reconstruction if both grades are explicitly available.

- Definition
- h_grade_root
- glottal_grade_root (Optional)
- Class ID
- Metadata:
  - `stem_type` (e.g. `con`, `vowel_a`)
  - `metathesis_strategy`
  - `set_a_b`
  - `use_ka_variant`, `use_uwa_for_3rd_set_b`, `use_aki_for_1st_set_b`
  - `use_3rd_person_object` (Implies 2->3 and 1->3 interaction)
  - `translocutive` (T), `partitive` (P), `distributive` (D).

### 2. Reconstruction (Generation)

The generator functions as the inverse of the stem derivation and classification process.

**Step 2a: Add Class Endings**
For each form (pres, imp, perf, imper, inf):
`Stem = Root + Class Suffix`

**Step 2b: Add Pronominal Prefix**

1.  Determine abstract prefix category (e.g., "3rd Set A") based on `Set`, `Imp Type` (2->3), and `Form`.
2.  Select specific prefix morph based on `Stem` phonology (vowel vs consonant).
    - **Ambiguity Handling**: If multiple prefixes are valid for a condition (e.g., `a-` vs `ka-` for consonants), generate _all_ valid variants.

**Step 2c: Add Prepronominal Prefixes**
Apply in order: `Distributive` -> `Partitive` -> `Translocutive` (Inner to Outer).
`Form = T(P(D(Pronoun(Stem))))`

_Phonological Rules:_ Handle `h` deletion/insertion and vowel coalescence in reverse of the stripping logic.

**Step 2d: H-Metathesis (If Applicable)**
If the verb is flagged as using metathesis in `stem_corpus.csv`, apply the metathesis variants:

- **Consonant**: `ka-` + `nhogi` -> `kanhogi` -> `khanhogi` (via metathesis-like aspiration)
- **Vowel**: `k-` + `ehlatitoh` -> `khelatitoh`, `uw-` + `ehlatitoh` -> `uwhelatitoh`, `h-` + `ehlatita` -> `helatita`
- If the verb is _not_ flagged, these metathesized variants are skipped to avoid over-application.

### 3. Validation

**Input**: Generated forms and `artifacts/corpus.csv` (Reference).

**Logic**:

- For each verb, check if the Reference form (from `corpus.csv`) is present in the set of Generated forms.
- If the reference form matches any of the generated variants, the reconstruction is considered successful.

## Ambiguity Resolution

1.  **Prefix Variants**: The generator produces **all valid prefix variants** for a given condition (e.g., both `a-` and `ka-`).
2.  **Consistency Constraint**: The _same_ variant must be used across all forms of a specific verb if the condition applies to multiple forms. Verification checks consistency at the outer level.
