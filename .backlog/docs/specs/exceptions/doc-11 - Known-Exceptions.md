---
id: doc-11
title: Known Exceptions
type: specification
created_date: '2026-06-10 16:29'
---

# Known Exceptions and Edge Cases

This document records known exception cases in the linguistic classification and reconstruction pipeline that deviate from standard rule patterns.

## Resolved Exceptions

### 1. "To order" (Corpus ID 46)
- **Status**: Resolved
- **Description**: Originally noted as having class `ohsk` but with `v` instead of `o`.
- **Resolution**: Successfully resolved by identifying it under the `sk-s-la` aspect class, which reconstructs.
- **Corpus entry**:
  ```csv
  corpus_id,entry_no,definition,present,present_1sg,imperfective,perfective,imperative,infinitive
  46,50,he/she is ordering it,atanvhsk,katanvhsk,atanvhsk,utanvhs,hatanvla,utanvhst
  ```

## Active Exceptions (Failing Reconstruction)

### 1. "To brag" (Corpus ID 100)
- **Status**: Failing (Stops at `2.pre_stripped` stage)
- **Reason**: Has class `sk-s-hihst`, but the sequence between the h-final root and the `h` in the class makes this fail (it expects immediate suffix `-ha` instead of `-a`). We parse this root-final `h` as part of the stem-ending.
- **Error**: `imperative: expected 'hatlvkwha', got ['hatlvkwa']`
- **Corpus entry**:
  ```csv
  corpus_id,entry_no,definition,present,present_1sg,imperfective,perfective,imperative,infinitive
  100,104,he/she is bragging,atlvkwhsk,katlvkwahsk,atlvkwhsk,utlvkwhs,hatlvkwha,utlvkwhihst
  ```

### 2. "To root out" (Corpus ID 1227) and "To boil" (Corpus ID 311)
- **Status**: Failing (Stops at `2.pre_stripped` stage)
- **Reason**: These rows have a `tl` which has its vowel cut and is then deaffricated before a consonant. This leaves a hard-to-explain `tl -> tlh -> lh` transformation. Both verbs are classified under the `ih-vh` class.
- **Errors**:
  - For "To root out" (1227): `infinitive: expected 'unhahstelhti', got ['unhahstetlhti']`
  - For "To boil" (311): Fails stem derivation.
- **Corpus entries**:
  ```csv
  corpus_id,entry_no,definition,present,present_1sg,imperfective,perfective,imperative,infinitive
  311,318,it’s boiling,alitlih,,alitlihsk,ulitlvh,,ulilht
  1227,1278,he/she is rooting it out,khanahstetlih,tsinahstetlih,khanahstetlihsk,unhahstetlvh,hinhahstetla,unhahstelht
  ```
