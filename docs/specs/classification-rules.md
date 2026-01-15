# Classification Rules

This document defines the criteria for matching verbs in the corpus to King's Conjugation Classes. For details on how classes are defined and expanded from data, see [Class Macros](class-macros.md).

## Match Matrix

We define a 2x2 matrix of match types based on **Strictness** and **Scope**.

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
- **Pass Condition**: All 5 forms (Present, Imperfective, Perfective, Imperative, Infinitive) must end with their respective pattern suffixes.

#### B. Full Match

Checks if _every function form_ is valid according to the class's `stem final` constraints.

- **Per-Form Logic**:
  1. Identify the literal ending in the class pattern.
  2. Strip this ending from the corpus form to reveal a "Candidate Stem".
  3. Adjust the class's `stem final` based on the pattern's modifier:
     - `*`: Remove the last character of the `stem final`.
     - `@`: Remove the last 2 characters of the `stem final` (or more, per rule).
  4. Verify that the "Candidate Stem" ends with the (adjusted) `stem final`.
- **Pass Condition**: All 5 forms must satisfy both the Ending Match _and_ the per-form Stem Final check.

#### C. Reconstructs Scope

The highest tier of matching, indicating that a verb can be perfectly derived from a single root across all available forms.

- **Logic**:
  1. Must pass **Strict Full Match**.
  2. Each form's stem must yield an identical "root" string when the class ending (including `*` and `@` modifiers) is stripped.
- **Pass Condition**: Strictly consistent root across all non-null corpus forms.
