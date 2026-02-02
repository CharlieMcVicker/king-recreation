# Middle Voice Infixes Specification

Middle voice infixes are reflexive or mediopassive markers that occur immediately preceding the verb root. They are used to indicate that the subject is both the actor and the undergoer of the action, or to indicate a state.

## Infix Forms

| Form          | Variation     | Lexical Environment     | Combined Stem Type  |
| :------------ | :------------ | :---------------------- | :------------------ |
| **at / atat** | `at` (short)  | Before vowels           | Vowel-initial ('a') |
|               | `atat` (long) | Before vowels           | Vowel-initial ('a') |
| **ata**       | `ata`         | Before consonants       | Vowel-initial ('a') |
| **ali / al**  | `ali`         | Before consonants       | Vowel-initial ('a') |
|               | `al`          | Before aspirated sounds | Vowel-initial ('a') |

## Structural Position

The infix occupies a slot between the pronominal prefix and the root:

`[Pre-pronominal Prefixes] ; [Pronominal Prefix] ; [Middle Voice Infix] ; [Root] ; [Aspect Suffixes]`

## Phonological Interactions

1.  **Stem Quality**: Verbs with a middle voice infix always behave as **vowel-initial stems** (specifically 'a' type) from the perspective of the pronominal prefix, regardless of the root's initial sound.
2.  **Infix Selection**: The selection between `at/atat`, `ata`, and `ali/al` is lexically determined (per verb).
3.  **Surface Variation**: The variation within a type (e.g., `at` vs `atat`) may be determined by aspect or syllable weight.

## Parsing Logic (Stem Derivation)

During the derivation of stems from corpus forms:

1.  Strip aspect suffixes.
2.  Strip pre-pronominal prefixes.
3.  Strip pronominal prefixes.
4.  **NEW**: Identify and strip the middle voice infix if present, immediately preceding the remaining root.

## Reconstruction Logic

During the reconstruction of forms from roots:

1.  Start with the root.
2.  **NEW**: Attach the appropriate middle voice infix based on the verb's configuration.
3.  Apply pronominal prefixes to the resulting infix-root combination (treating it as an 'a' vowel stem).
4.  Apply pre-pronominal prefixes.
5.  Apply aspect suffixes.
