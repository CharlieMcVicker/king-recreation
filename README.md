# Recreating Duane King's 1975 classification of aspect endings in Cherokee verbs

This project will apply Duane King's 1975 classification scheme of aspect inflection in Cherokee verbs to the Cherokee-English Dictionary (Pulte and Feeling 1975) corpus. Because tonal and vowel length marking systems are not consistent between King 1975 and Feeling 1975, vowel length is not considered for matching. In addition, glottal stops are not considered for matching, since their marking and surface realization is not comparable between the two dialects and dictionaries.

## Process

### CED pre-processing

To deal with differences in orthography as well as what information is recoreded, the corpus will be pre-processed. The data from the Cherokee-English Dictionary, in `ced_data_original.csv` will be read into memory. All tone markings `/[1234\.]/` and glottal stops `/\?/` will be dropped. The reference forms considered for this study will be:

1. "Present" (`3rd present` column)
2. "Imperfective" (`3rd incompletive habitual` column with `oi` rstripped)
3. "Perfective" (`3rd completive past` column with `vi` rstripped)
4. "Imperative" (`2nd imperative` column)
5. "Infinitive" (`3rd infinitive` column with `i` rstripped)

This file is then written to disk as `corpus.csv`