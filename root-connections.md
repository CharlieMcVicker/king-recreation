# Root connections

Some verbs are more complex than others. What we are currently identifying as the "root" of a verb may actually be either a perfective or infinitive of another verb. To find such cases we will create a list of possible "open forms" which might be appearing as the "roots" of other verbs. To do this, we will use parts of the reconstruction engine. We will do this by making sure the reconstruction engine is broken into good clean parts. We will need to be able to take a reconstructable verb and:

1. Add the perfective or infinitive ending to make the perfective or infinitive stem of the verb (with no pronoun or pre-pronoun prefixes on it)
2. Be able to generate the possible h-alternated version of this stem (using `possible_alternates`)

We should keep this list of open forms in memory. Then, we will check the list of reconstructable verbs for roots which are on this list. We will create a data file in `artifacts/` capturing which verb roots seem to be built on open forms of other roots.

We will do this as a new step in our pipeline that happens right before analysis and visualization.

## Test case

"Visiting" (corpus id 208) is built on top of the perfective of "Finding" (id 207). We should make sure we flag this.
