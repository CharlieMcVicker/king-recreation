# H-Alternation Simplification

We are going to revise how we handle `/h/` alternation. We will no longer attempt to re-insert `/h/`s programatically. Instead, we will use the `present_1sg` form to determine how `/h/` alternation happens.

## Root Grades

Instead of considering a single root which produces all forms, we will allow for two "grades" of root:

1.  **h-grade**: The unalternated stem, used by all third person forms, and the 2nd imperative (unless 3rd person objects are used).
2.  **glottal-grade**: The `/h/` alternated stem, which can be deduced from `present_1sg` if either:
    1.  Set A pronouns are used.
    2.  Third person objects are used to indicate an object.

In the case that the glottal grade root cannot be deduced, it should not matter because no documented forms will be built on the glottal grade root.

## Root Positing Strategy

For positing roots, we will use the present tense forms for each grade and remove suffixes:

- **h-grade**: Derived from 3rd person present.
- **glottal-grade**: Derived from 1st person present.

This gives us a root candidate for each grade. Forms will then be checked against the matching grade root for their reconstruction.

### Grade Assignment Table

The grade to use for each form is as follows:

| Form               | Grade                                                               |
| :----------------- | :------------------------------------------------------------------ |
| `present` (3rd)    | **h-grade**                                                         |
| `present_1sg`      | **h-grade** if Set B<br>**glottal-grade** if Set A or to 3rd person |
| `incompletive`     | **h-grade**                                                         |
| `completive`       | **h-grade**                                                         |
| `imperative` (2nd) | **h-grade** if Set A/B<br>**glottal-grade** if to 3rd person        |
| `infinitive`       | **h-grade**                                                         |

## Implementation Details

The strategy is implemented as a **Dual Grade** root system in the reconstruction pipeline.

### Root Extraction

Roots are extracted from `stem_corpus.csv` using the following logic:

- **h-grade root**: Derived from the `present` form (3rd person).
- **glottal-grade root**: Derived from the `present_1sg` form. If the class definition lacks a `present_1sg` suffix pattern, the system defaults to using the `present` suffix pattern for stripping.

### Verification (Consistency Check)

The consistency check is defined as:
`drop_first_h(h_grade_root) == glottal_grade_root`

- **H-Dropping**: The `/h/` is ONLY dropped from the h-grade root. The glottal-grade root is compared as-is.
- **Reporting**: Mismatches are logged in `artifacts/reports/consistency_analysis.csv`. This flags verbs that do not follow the standard h-dropping/retention patterns for manual review.

### Grade Selection Logic

The reconstruction engine selects the root to use for each form based on the verb configuration (`PronominalConfig`):

- **Default**: Use **h-grade root**.
- **Glottal Grade Exceptions**:
  - `present_1sg`: Used if the prefix set is `1st Set A` or `1st to 3rd` (1st person transitive).
  - `imperative`: Used if the prefix set is `2nd to 3rd` (2nd person transitive with 3rd person object).

## Stem Derivation Adjustments

To support this system, `king_recreation/derive_stems.py` was updated to skip consistency checks for `imperative` forms when `use_3rd_person_object` is enabled. This allows the imperative to diverge from the consensus (h-grade) stem and correctly reflect the glottal grade when required.
