# Preprocessing Specifications

The corpus is pre-processed to standardize orthography and filter information not relevant to the current study.

## Source Data

The pipeline supports two primary input sources:

1.  **CED Data**: `data/ced_data_original.csv`. This is the default source.
2.  **Cherokee Nation Dictionary (CND)**: `data/cherokee_nation_dictionary.csv`. Used when the `--new-source` flag is provided. This source groups multiple rows by "No." and prioritizes "animate" or "3rd person object" forms where multiple variations exist for a single slot.

## Normalization Rules

Preprocessing involves standardizing the input text via the following rules:

### 1. Orthography

- **Tone & Length**: All tone markings `/[1234\.]/` are dropped. (Note: Length marking is also not preserved).
- **Glottal Stops**: Glottal stops represented as `?` or `’` are converted to standard apostrophes `'`.

### 2. Consonant Respellings

Consonants are respelled to mark aspiration explicitly and standardize clusters:

| Original | Respelled                               |
| :------- | :-------------------------------------- |
| `t`      | `th` (except before `s`)                |
| `d`      | `t`                                     |
| `k`      | `kh`                                    |
| `g`      | `k`                                     |
| `j`      | `ts`                                    |
| `ch`     | `tsh`                                   |
| `hl`     | `lh`                                    |
| `hn`     | `nh`                                    |
| `hy`     | `yh`                                    |
| `hw`     | `wh`                                    |
| `sl`     | `slh` (before vowels `[aeiou]`)         |
| `s`      | `hs` (after any char except `h` or `t`) |

## Reference Forms

The study considers 6 reference forms. Each entry is assigned a unique `corpus_id`.

| Form ID          | Source Column (CED)         | Processing (Suffix Stripping)                      |
| :--------------- | :-------------------------- | :------------------------------------------------- |
| **Present**      | `3rd present`               | `i` or `a` rstripped (for `i'a`, only `a` dropped) |
| **Present 1sg**  | `1st present`               | `i` or `a` rstripped (for `i'a`, only `a` dropped) |
| **Imperfective** | `3rd incompletive habitual` | `o'i` rstripped                                    |
| **Perfective**   | `3rd completive past`       | `v'i` rstripped                                    |
| **Imperative**   | `2nd imperative`            | None (Keep as is)                                  |
| **Infinitive**   | `3rd infinitive`            | `i` rstripped                                      |
