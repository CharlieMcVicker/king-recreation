# Class Macros

To streamline the definition of interrelated verb classes, the system supports **macro expansion** in the class definition data (`data/classes.csv`). This allows a single row to represent multiple class variants by providing multiple options for specific functional forms.

## Expansion Rules

1.  **Separator**: Options within a cell are separated by a semicolon (`;`).
2.  **Cartesian Product**: The system generates a new class variant for every possible combination of options across all functional fields.
3.  **Naming Convention**:
    - The **base class name** is used for the combination using the first option from every field.
    - Subsequent variants append a bracketed suffix containing shorthands and indices for any non-first options used.
    - Shorthands: `pres`, `imperf`, `perf`, `imp`, `inf`.
    - Example suffix: `[perf2-inf3]` (indicates the 2nd perfective option and 3rd infinitive option).
    - Tags are ordered by column: present, imperfective, perfective, imperative, infinitive.
4.  **Exception**: The `stem final` field supports semicolon-separated lists but **does not** trigger expansion. Instead, the full list of stem finals is shared across all expanded variants of that class.

## Example

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

## Implementation

Expansion occurs dynamically during class loading in `ClassPatterns.from_csv`. This ensures that classification and reconstruction logic can treat expanded variants as standard, independent classes.
