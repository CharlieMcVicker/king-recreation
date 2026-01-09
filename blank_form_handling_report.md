# Report: Handling of Blank Forms in the Pipeline

This report describes how the current pipeline handles verb entries with missing or incomplete aspect paradigms (referred to as "blank forms").

## Overview

A "blank form" occurs when one or more of the five required aspect forms (Present, Imperfective, Perfective, Imperative, Infinitive) is missing in the source data. A prime example is the verb entry for **"He is getting in a car, box, etc"**, which has a blank entry for the infinitive form.

## Pipeline Breakdown

The following sections describe how different components of the pipeline interact with these blank forms.

### 1. Preprocessing (`preprocess_ced.py`)

- **Action**: Converts "no data" markers (such as `-----` or `None`) into empty strings (`""`) in the `artifacts/data/corpus.csv`.
- **Approach**: Normalization. It preserves the record but marks the specific form as empty.

### 2. Verb Classification (`classify_verbs.py`)

- **Action**: Verbs with any empty form are **strictly excluded**.
- **Logic**: The `get_matches_for_verb` function checks `if not form_val`. If any form is empty, it sets `all_endings_match = False` and breaks early.
- **Result**: These verbs never appear in `artifacts/data/matches.csv` as full or partial matches.

### 3. Stem Derivation (`derive_stems.py`)

- **Action**: Verbs with fewer than 5 forms are **dropped**.
- **Logic**: The script checks `if len(forms) < 5: return []` at the start of derivation.
- **Result**: Blank-form verbs are logged as failures in `artifacts/debug/derivation_failures.json` and are absent from `artifacts/data/stem_corpus.csv`.

### 4. Analysis and Reporting (`analyze_matches.py`)

- **Action**: Verbs with blank forms are counted as **unmatched**.
- **Approach**: Total coverage calculations include all verbs in the corpus. Since blank-form verbs are never matched, they are categorized as "0 matches" in `artifacts/reports/verb_coverage.json`.
- **Result**: They are exported to `artifacts/reports/unmatched_verbs_strict.csv`, where they can be manually inspected.

### 5. Reconstruction (`reconstruct_from_roots.py`)

- **Action**: **Complete exclusion**.
- **Logic**: Reconstruction depends on the output of `derive_stems.py`. Since blank-form verbs are dropped during derivation, they are never processed for reconstruction.

---

## Consistency Analysis

The handling of blank forms is **consistent in execution but inconsistent in interpretation**:

| Component          | Consistency | Interpretation                                                                                                     |
| :----------------- | :---------- | :----------------------------------------------------------------------------------------------------------------- |
| **Data Integrity** | High        | Preserved in the corpus as empty fields.                                                                           |
| **Logic Layer**    | High        | Consistently rejected by classification and derivation.                                                            |
| **Reporting**      | Mixed       | Included in the denominator for statistics, effectively treated as "matching failures" rather than "missing data." |

### Different Approaches Observed

1. **The "Strict Paradigm" Approach**: Most scripts (classification, derivation, reconstruction) assume a complete 5-form set is mandatory for any meaningful linguistic analysis. Any deviation is treated as a fatal error for that specific verb.
2. **The "Inclusive Denominator" Approach**: Reporting scripts include these incomplete paradigms in the total verb count, which intentionally or unintentionally lowers overall coverage scores.

## Conclusion

The pipeline currently adopts a **fail-fast** approach for incomplete paradigms. While this ensures the mathematical integrity of class matching and stem derivation, it means that verbs like "getting in a car" (which are linguistically valid but may have accidental data gaps) are systematically excluded from the system's output.
