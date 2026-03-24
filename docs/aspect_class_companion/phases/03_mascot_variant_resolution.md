# Phase 3: Mascot Variant Resolution

## Goal
Dynamically determine the strictly occurring combinations of variant morphologies for each aspect class, and assign a stable "mascot" verb (with its 5 reference forms) to each.

## Context
Aspect classes can technically combine with many variant prefixes or suffixes, but we only want to document combinations that actually appear in the Cherokee corpus. Furthermore, mascot selection must be completely deterministic so rebuilds don't visually shift the document unless new data is added.

## Step-by-Step Implementation
1. **Module Creation:**
   - Create `tex_dictionary/mascot_resolver.py`.
2. **Corpus Base Querying:**
   - Import necessary dictionary data (e.g., `artifacts/data/reconstructable_verbs.json` or by utilizing `load_hierarchical_data()` from `generator.py`).
   - For a given `aspect_class` (like `sk-s`), aggregate *all* verbs in the dictionary that belong to this class.
3. **Extracting Occurring Variants:**
   - Iterate through the aggregated verbs and inspect their configurations (`verb.config`).
   - Build a `Set` of distinct variant combinations observed (e.g., "Plain", "Translocutive + Plain", "Partitive + Middle Voice"). This prevents documenting hypothetical variants.
4. **Mascot Resolution Logic:**
   - For *each* distinct variant combination found for the class:
     - Check `curated/aspect_class_mascots.csv` to see if the user manually mapped a `mascot_corpus_id` to this class/subclass/variant.
     - If yes: Retrieve that exact `ReconstructableVerb`.
     - If no: Filter the aggregated verbs down to just those matching this specific variant combination. Sort them alphabetically by their plain *toneless Present* form. Select the 1st verb in the list.
5. **Reference Form Fetching:**
   - Use functions modeled from `generator.py`'s `generate_verb_table()` to retrieve the Mascot's Present, Imperfective, Perfective, Imperative, and Infinitive forms from `corpus_to_cnd.csv` and `cherokee_nation_dictionary.csv`.
6. **Validation:**
   - Verify that running the resolver on a common class like `cause` yields the base variant along with specific actually-occurring variants, and correctly retrieves the 5 conjugated forms for the alphabetically-first verb.
