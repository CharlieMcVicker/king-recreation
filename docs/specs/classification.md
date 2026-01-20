# Classification Specifications

This document defines the structure of King's Conjugation Classes and the rules for matching verbs in the corpus to these classes.

## Class Macros

To streamline the definition of interrelated verb classes, the system supports **macro expansion** in the class definition data (`data/classes.csv`). This allows a single row to represent multiple class variants by providing multiple options for specific functional forms.

### Expansion Rules

1.  **Separator**: Options within a cell are separated by a semicolon (`;`).
2.  **Cartesian Product**: The system generates a new class variant for every possible combination of options across all functional fields.
3.  **Naming Convention**:
    - The **base class name** is used for the combination using the first option from every field.
    - Subsequent variants append a bracketed suffix containing shorthands and indices for any non-first options used.
    - Shorthands: `pres`, `imperf`, `perf`, `imp`, `inf`.
    - Example suffix: `[perf2-inf3]` (indicates the 2nd perfective option and 3rd infinitive option).
    - Tags are ordered by column: present, imperfective, perfective, imperative, infinitive.
4.  **Exception**: The `stem final` field supports semicolon-separated lists but **does not** trigger expansion. Instead, the full list of stem finals is shared across all expanded variants of that class.

### Example

A macro definition like:

| class | stem final | present | perfective | infinitive   |
| :---- | :--------- | :------ | :--------- | :----------- |
| hvsk  |            | hvsk    | nh;han     | ht;\*ht;hvst |

Expands into 6 distinct classes:

1.  `hvsk`: (nh, ht)
2.  `hvsk[inf2]`: (nh, \*ht)
3.  `hvsk[inf3]`: (nh, hvst)
4.  `hvsk[perf2]`: (han, ht)
5.  `hvsk[perf2-inf2]`: (han, \*ht)
6.  `hvsk[perf2-inf3]`: (han, hvst)

### Implementation Note

Expansion occurs dynamically during class loading in `ClassPatterns.from_csv`. This ensures that classification and reconstruction logic can treat expanded variants as standard, independent classes.

---

## Match Matrix

Classification uses a 2x2 matrix of match types based on **Strictness** and **Scope**.

### 1. Strictness Levels

| Level      | Description                                                                                                 |
| :--------- | :---------------------------------------------------------------------------------------------------------- |
| **Strict** | The form from the corpus must match the class pattern exactly (after rule application).                     |
| **Loose**  | Both the corpus form and the class pattern are normalized by removing all `h` characters before comparison. |

### 2. Match Scopes

#### A. Ending Match

Checks if the _ends_ of the corpus forms match the literal ending characters specified in the class pattern.

- **Constraints**:
  - For patterns with modifiers (e.g., `*a`), only the literal characters are matched (e.g., must end in `a`). The modifier is ignored.
  - Empty cells in the class definition imply an empty ending (match bare stem).
- **Pass Condition**: All 5 primary forms (Present, Imperfective, Perfective, Imperative, Infinitive) must end with their respective pattern suffixes.

#### B. Full Match

Checks if _every functional form_ is valid according to the class's `stem final` constraints.

- **Per-Form Logic**:
  1. Identify the literal ending in the class pattern.
  2. Strip this ending from the corpus form to reveal a "Candidate Stem".
  3. Adjust the class's `stem final` based on the pattern's modifier:
     - `*`: Remove the last character of the `stem final`.
     - `@`: Remove the last 2 characters of the `stem final`.
  4. Verify that the "Candidate Stem" ends with the (adjusted) `stem final`.
- **Pass Condition**: All 5 forms must satisfy both the Ending Match _and_ the per-form Stem Final check.

#### C. Reconstructs Scope

The highest tier of matching, indicating that a verb can be perfectly derived from a single root across all available forms. This scope is only assigned during the validation phase of the [Reconstruction](reconstruction.md) pipeline.

- **Logic**:
  1. Must pass **Strict Full Match**.
  2. The verb must be successfully processed by the [Stem Derivation](stem-derivation.md) engine to extract a consistent root.
  3. The [Reconstruction](reconstruction.md) engine must be able to exactly reproduce all corpus forms from that root and class.
- **Pass Condition**: Strictly consistent root across all non-null corpus forms, verified by generation.
