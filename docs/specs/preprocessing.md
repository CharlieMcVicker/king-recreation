# Preprocessing Specifications

The corpus is pre-processed to standardize orthography and filter information not relevant to the current study.

## Normalization Rules

### 1. Orthography

The `ced_data_original.csv` is processed with the following rules:

- **Tone & Length**: All tone markings `/[1234\.]/` and glottal stops `/\?/` are dropped. (Note: Length marking is also not preserved).

### 2. Consonant Respellings

Consonants are respelled to mark aspiration explicitly:

| Original | Respelled |
| :------- | :-------- |
| `t`      | `th`      |
| `d`      | `t`       |
| `k`      | `kh`      |
| `g`      | `k`       |
| `j`      | `ts`      |
| `ch`     | `tsh`     |

## Reference Forms

The study considers the following 5 reference forms, derived as follows:

| Form ID          | Source Column               | Processing                                        |
| :--------------- | :-------------------------- | :------------------------------------------------ |
| **Present**      | `3rd present`               | `i` or `a` rstripped (for `ia`, only `a` dropped) |
| **Imperfective** | `3rd incompletive habitual` | `oi` rstripped                                    |
| **Perfective**   | `3rd completive past`       | `vi` rstripped                                    |
| **Imperative**   | `2nd imperative`            | None (Keep as is)                                 |
| **Infinitive**   | `3rd infinitive`            | `i` rstripped                                     |
