# Recreating Duane King's 1975 classification of aspect endings in Cherokee verbs

This project will apply Duane King's 1975 classification scheme of aspect inflection in Cherokee verbs to the Cherokee-English Dictionary (Pulte and Feeling 1975) corpus. Because tonal and vowel length marking systems are not consistent between King 1975 and Feeling 1975, vowel length is not considered for matching. In addition, glottal stops are not considered for matching, since their marking and surface realization is not comparable between the two dialects and dictionaries.

## Process

### CED pre-processing

To deal with differences in orthography as well as what information is recoreded, the corpus will be pre-processed. The data from the Cherokee-English Dictionary, in `data/ced_data_original.csv` will be read into memory. All tone markings `/[1234\.]/` and glottal stops `/\?/` will be dropped.

Consonants will be respelled to mark aspiration explicitly:

- `t` -> `th`
- `d` -> `t`
- `k` -> `kh`
- `g` -> `k`

The reference forms considered for this study will be:

1. "Present" (`3rd present` column with final `i` or `a` rstripped; for `ia` only `a` is dropped)
2. "Imperfective" (`3rd incompletive habitual` column with `oi` rstripped)
3. "Perfective" (`3rd completive past` column with `vi` rstripped)
4. "Imperative" (`2nd imperative` column)
5. "Infinitive" (`3rd infinitive` column with `i` rstripped)

This file is then written to disk as `artifacts/corpus.csv`

### King's classes

King's classes are stored in `data/king_classes.csv` (note: filename corrected from `kings_classes.csv`). Glottal stops have been removed from his original tables. Length marking has also been removed.

**Goal:** Classify each verb in `artifacts/corpus.csv` by comparing it against every class pattern in `data/king_classes.csv`.

#### Match Criteria

We define two strictness levels and two scopes, creating a matrix of 4 possible match types.

**1. Strictness Levels**
*   **Strict:** The form from the corpus must match the class pattern exactly (after rule application).
*   **Loose:** Both the corpus form and the class pattern are normalized by removing all `h` characters before comparison.

**2. Match Scopes**
*   **Ending Match:** Checks if the *ends* of the corpus forms match the literal ending characters specified in the class pattern.
    *   For patterns with special symbols (e.g., `*a`), only the literal characters are matched (e.g., must end in `a`). The stem modification implied by `*` is ignored in this scope.
    *   Empty cells in the class CSV imply an empty ending (the form matches the bare stem).
    *   *Pass condition:* All 5 forms (Present, Imperfective, Perfective, Imperative, Infinitive) must end with their respective pattern suffixes.
*   **Full Match:** Checks if *every function form* is valid according to the class's `stem final` constraints.
    *   **Logic (Per Form):** for each of the 5 forms:
        1.  Identify the literal ending in the class pattern (ignoring `*` or `@`).
        2.  Strip this ending from the corpus form to reveal a "Candidate Stem".
        3.  Adjust the class's `stem final` based on the pattern's modifier:
            *   `*`: Remove the last character of the `stem final`.
            *   `@`: Remove the last 2 characters of the `stem final` (or more, per rule).
        4.  Verify that the "Candidate Stem" ends with the (adjusted) `stem final`.
    *   *Pass condition:* All 5 forms must satisfy both the Ending Match and the per-form Stem Final check.

#### Output
For each verb in the corpus, if a match is found, append a row to `artifacts/matches.csv` with:
1.  `definition`: From corpus.
2.  `class`: The matched class ID (e.g., `Ia`, `IIb`).
3.  `strictness`: `strict` or `loose`.
4.  `scope`: `ending` or `full`.
5.  `stem_final_match_present`: Boolean.
6.  `stem_final_match_imperfective`: Boolean.
7.  `stem_final_match_perfective`: Boolean.
8.  `stem_final_match_imperative`: Boolean.
9.  `stem_final_match_infinitive`: Boolean.

> **Important:** Even if a "Full Match" fails (resulting in a scope of "Ending"), the `stem_final_match_*` columns **must** still be calculated and populated. This is crucial for debugging near-matches and identifying data quality issues.

Note: A single verb may have multiple matches (e.g., one Strict/Full and one Loose/Ending).

### Match data analysis

The data in `artifacts/matches.csv` contains rich information about how well the King classification scheme accounts for the CED corpus. A script `king_recreation/analyze_matches.py` processes this data to generate three distinct metrics.

**Usage:** `python3 -m king_recreation.analyze_matches [--visualize]`
-   `--visualize`: If set, automatically runs the visualization script after analysis is complete.

**Technical Note on `matches.csv`:**
A single verb (`definition`) can match multiple classes and strictnesses. However, for a given `(verb, class, strictness)`, only the *largest* achieved scope is recorded as a single row. If a "Full" match is achieved, there should not be a separate "Ending" row for that specific combination. 

**1. Class-wise Match Counts**
Calculate the total number of unique verbs matched by each class, broken down by all four strictness/scope combinations. 
-   **Output**: `artifacts/class_match_counts.csv`
-   **Columns**: `class`, `strict_ending`, `strict_full`, `loose_ending`, `loose_full`
-   **Logic**: `strict_ending` counts verbs that matched *only* at the ending level for that class, while `strict_full` counts those that passed the full stem-final check. (Note: Scripts should implement a safety check to ensure they are counting the largest scope per verb/class).

**2. Verb Coverage Summary**
Analyze how well the King classification explains the total corpus.
-   **Denominator**: Total number of unique verbs (definitions) in `artifacts/corpus.csv`.
-   **Output**: `artifacts/verb_coverage.json`
-   **Structure**: For each strictness/scope combination, count how many verbs are matched by zero, one, or multiple classes.
    ```json
    {
      "strict_full": { "0": 1200, "1": 300, "2+": 50 },
      "loose_full": { ... },
      ...
    }
    ```

**3. Class Near-Miss Analysis**
For verbs that achieve an `ending` match but fail a `full` match for a given class, identify which functional forms are the primary "blockers."
-   **Output**: `artifacts/class_near_misses.csv`
-   **Metric**: For each `(class, strictness)` pair, filter for rows where `scope == "ending"`. Calculate the "Pass Rate" (0.0 to 1.0) for each of the 5 stem-final columns.
-   **Columns**: `class`, `strictness`, `match_count`, `present_rate`, `imperfective_rate`, `perfective_rate`, `imperative_rate`, `infinitive_rate`.

### Visualization

To help interpret the results, a separate script `king_recreation/visualize_analysis.py` generates charts using `matplotlib` and `seaborn`.

**Usage:** `python3 -m king_recreation.visualize_analysis`
-   The script generates both "full" and "filtered" versions of charts automatically to handle clutter.

**Generated Plots:**
1.  **Class Distribution** (`artifacts/class_distribution_full.png`, `artifacts/class_distribution_filtered.png`): A bar chart showing the number of verbs matched by each class, clustered by strictness/scope.
2.  **Coverage Overlap** (`artifacts/verb_coverage.png`): A visualization of the "Verb Coverage Summary."
3.  **Near-Miss Heatmap** (`artifacts/near_miss_heatmap_full.png`, `artifacts/near_miss_heatmap_filtered.png`): A heatmap showing which forms are the most frequent blockers.

## Ongoing Work & Side-Quests

This section tracks items for verification and refinement following the initial implementation:

-   **Data Integrity Check**: Verify that `king_recreation/classify_verbs.py` strictly enforces the "largest scope only" rule when writing `matches.csv`. If redundant "Ending" rows exist for verbs that also have "Full" rows, update the script to suppress them.
-   **Visual Review**: Evaluate the readability of the Near-Miss Heatmap with and without the clutter-avoidance flag.
-   **Style Consistency**: Confirm preference for `matplotlib` styling (default vs. `seaborn` or `ggplot`) after reviewing initial plots.