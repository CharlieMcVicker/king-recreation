# 1st vs 3rd Person Root Guesses Report

This report documents the current logic handling 1st person present vs 3rd person present root derivation and usage within the pipeline.

## 1. Stem Derivation Logic (`derive_stems.py`)

The stem derivation process distinguishes between "Consensus" stems (derived mainly from 3rd person forms) and "1st Person" stems.

### 3rd Person (Consensus) Stem

The "Target" stem is derived from non-h-dropping forms. In practice, for most verbs, these are the 3rd person forms (Present, Imperfective, Perfective, etc.). The system seeks a single stem that explains all these forms.

### 1st Person (Split Stem) Handling

The 1st Person Singular Present (`present_1sg`) is treated with special logic:

1.  **Strict Check**: The system attempts to match `present_1sg` candidates against the Consensus Stem using strict compatibility.
2.  **Fallback "Guess"**: If the 1st person form _cannot_ be explained by the Consensus Stem (indicating a "split stem" or irregularity), the derivation **does not fail**.
    - Instead, the system "guesses" a separate stem for `present_1sg`.
    - **Selection Criteria**: It selects the literal candidate from `present_1sg` that has the **longest common prefix** with the Consensus Stem.
    - This separate stem is saved in the `present_1sg` column of `stem_corpus.csv`.

## 2. Usage in Reconstruction (`reconstruct_from_roots.py`)

Currently, the reconstruction engine **does not use** the 1st person root guesses.

- **Input Data**: The engine loads `stem_corpus.csv`.
- **Root Consistency**: The `check_root_consistency` function only considers the standard 5 forms: `['present', 'imperfective', 'perfective', 'imperative', 'infinitive']`. It explicitly excludes `present_1sg` from the consistency check.
- **Validation**: The validation loop verifies generated forms against the corpus, but it restricts validation to the same 5 standard forms.

**Conclusion**: The "1st person guess" data is currently generated and stored but is effectively **dormant** in the reconstruction and validation steps. The system currently assumes 1st person forms should be reconstructible from the main root, but doesn't verify this.
