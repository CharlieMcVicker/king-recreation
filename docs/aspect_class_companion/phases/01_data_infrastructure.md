# Phase 1: Data Infrastructure & Orchestration

## Goal
Establish the data foundation for the Aspect Class Companion by preparing the necessary mapping files and loading/sorting logic.

## Context
We need to map Cherokee aspect classes (defined in `data/classes.csv`) to specific "mascot" verbs that will illustrate the class paradigms. To ensure stability, we rely on a curated CSV mapping file and fallback to deterministic alphabetical selection. We also want to present the most common aspect classes first for pedagogical reasons.

## Step-by-Step Implementation
1. **Create Curated Mascot Template:**
   - Create a new file at `curated/aspect_class_mascots.csv`.
   - Ensure it has the headers: `class`, `subclass`, `mascot_corpus_id`.
   - (Optional) Populate a few known mascots if available, otherwise commit the empty template with headers.
2. **Path Configuration:**
   - Add `ASPECT_CLASS_MASCOTS_PATH` pointing to `curated/aspect_class_mascots.csv` in `king_recreation/paths.py`.
   - Add `COMPANION_TEX_PATH` pointing to `artifacts/tex/companion.tex` in `king_recreation/paths.py`.
3. **Data Loading Module:**
   - Create a foundational Python module (e.g., `tex_dictionary/companion_data.py`).
   - Implement a function `load_aspect_classes()` that parses `data/classes.csv` and returns a list of dictionaries/dataclasses representing the surface forms of the endings (Present, Imperfective, Perfective, Imperative, Infinitive).
4. **Sorting by Frequency:**
   - Implement `sort_classes_by_frequency(classes)` in the data module.
   - Read `artifacts/reports/class_match_counts.csv`. Sum the values (e.g., `reconstructs` column) for each class/subclass.
   - Sort the list of aspect classes in descending order of empirical frequency.
5. **Validation:** Ensure the loader outputs exactly ~56 classes and that the `cause` and `stative` paradigms float to the top of the sorted list.
