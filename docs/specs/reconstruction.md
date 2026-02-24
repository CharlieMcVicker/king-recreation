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

The process begins by reading `curated/validated_reconstructable_roots.csv` (or `derived_roots.csv` for initial runs) and `artifacts/data/corpus.csv`. The input file contains verbs with their identified classes, extracted roots, and configuration flags.

**Logic:**

1.  **Input**: Iterate through verbs in `derived_roots.csv`.
2.  **Dual Roots**: The system extracts two roots:
    - **h-grade root**: The unalternated base (from the `consensus_root` or `present` column), used for most forms.
    - **glottal-grade root**: The `/h/`-alternated base (from `present_1sg` if it uses Set A).
3.  **Grade Selection**: For each target form, the engine selects the appropriate grade using the `use_glottal_grade` logic:
    - **Glottal Grade**: Used for forms using the `1st Set A`, `1st to 3rd`, and `2nd to 3rd` pronominal sets.
    - **H-Grade**: Used for all other forms.
4.  **Compatibility Check**: Verifies that the roots are compatible using `grades_are_compatible`. This logic handles dropping the first `/h/`, glottalization (`h` -> `'`), deaffricative lateral shifts (`lh` -> `tl`), and vowel restoration heuristics.

**Reconstructible Verb Object:**

- Definition
- h_grade_root
- glottal_grade_root (Optional)
- Class ID (class_name)
- Config:
  - `stem_type` (e.g. `con`, `vowel_a`, `aspirated`, `s_stem`)
  - `allow_h_metathesis` (boolean)
  - `set_a_b` (`Set A` or `Set B`)
  - `use_ka_variant`, `use_uwa_for_3rd_set_b`, `use_aki_for_1st_set_b`
  - `use_3rd_person_object` (Implies 2->3 and 1->3 interaction)
  - `middle_voice` (Middle voice pattern to apply, e.g. `ali`, `ati`)
  - Prepronominal flags: `translocutive`, `partitive`, `distributive`, etc.

### 2. Reconstruction (Generation)

The generator functions as the inverse of the stem derivation and classification process.

**Step 2a: Add Class Endings**
For each form (present, present_1sg, imperfective, perfective, imperative, infinitive):

1. Determine the appropriate root grade.
2. Apply class endings from the pattern registry. Handle vowel coalescence markers (`*` for 1-vowel drop, `@` for 2-vowel drop).
3. **Middle Voice Application**: If `middle_voice` is configured, apply the middle voice transformation to the root (e.g. prefixing `ali-`, `ati-`) before prefix attachment.
4. Handle `/h/` alternation fallbacks: if glottal grade is required but no `h` was present in the root, attempt to apply alternation to the ending if applicable (e.g., via `possible_alternates`).

**Step 2b: Add Pronominal Prefix**

1. Determine abstract prefix category based on `Set`, `3rd Person Object` flag, and `Form`.
2. Select specific prefix morph based on `Stem` phonology and flags (`ka-`, `aki-`, `uwa-`).
3. **Ambiguity Handling**: If multiple prefixes/alternates are valid (e.g. via `possible_alternates`), generate a set of candidates.

**Step 2c: Add Prepronominal Prefixes**
Apply in order: `Distributive` -> `Partitive` -> `Translocutive`.
`Form = T(P(D(Pronoun(Stem))))`

**Step 2d: Metathesis Logic**

- **H-Metathesis**: If `allow_h_metathesis` is used, aspiration moves to the prefix (e.g., `ka-` + `nh...` -> `khanh...`).

### 3. Validation

**Input**: Generated candidate sets and `artifacts/data/corpus.csv` (Reference).

**Logic**:

- For each verb, check if the Reference form (from `corpus.csv`) is present in the set of Generated forms.
- If all reference forms match at least one generated variant, the reconstruction is successful.

### 4. Output Artifacts

- **reconstructable_verbs.json**: Fully serialized successfully reconstructed verbs for frontend use.
- **curated/validated_reconstructable_roots.csv**: The source of truth for user-validated roots and configurations.
- **reconstruction_report.csv**: Summary of success/failure and ambiguity for each verb.
- **reconstruction_failures.csv**: Detailed mismatch reports for failing verbs.
- **matches_validated.csv**: Subset of verified matches for downstream logic.

## Ambiguity Resolution

1.  **Candidate Sets**: The generator produces a set of all valid candidates for each form.
2.  **Validation**: Success is defined as the reference form existing within the set of candidates.
3.  **Consistency**: Verifies that the same class and root can generate all observed forms.
