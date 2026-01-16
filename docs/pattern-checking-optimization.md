# Pattern Checking Optimization

## Overview

We are optimizing the classification process by replacing the O(N\*M) "check every pattern against every verb" loop with an O(1) / O(K) lookup strategy. This involves refactoring how class patterns are stored and queried.

## Architecture

### 1. Data Structures

**`ClassMacro`**:

- Represents a raw row from the CSV.
- Stores fields (`present`, `imperfective`, etc.) as `List[str]` (parsed from CSV).
- Responsible for expanding itself into individual `ExpandedClassPattern` objects.

**`ExpandedClassPattern`** (formerly `ClassPatterns`):

- Represents a fully resolved pattern instance (single string per field).
- Used by the classification logic to check full verification (including Stem Finals).

### 2. Registry & Lookup

**`PatternRegistry`**:

- A module-level registry class (singleton usage pattern).
- **Responsibilities**:
  - `load_from_csv(path)`: Reads CSV into `ClassMacro`s.
  - `build_lookup_maps()`: functionality to index patterns for fast retrieval.
  - `get_candidates(verb_form, form_type) -> List[ExpandedClassPattern]`: Returns potential matches.

### 3. Lookup Strategy

The core optimization relies on a Reverse Lookup Map.

**Map Structure**:

- `Map<EndingString, List[Candidate]>`
- **Key**: The literal suffix string (with `*` and `@` removed).
- **Value**: A list of candidates that produce this ending.

**Lookup Algorithm**:

1. For a given verb form (e.g., "present"), we do not know the ending length.
2. We check suffixes of the verb against the map potentially, or (better) we iterate valid endings from the registry.
   - _Optimization_: Since the number of distinct endings is finite and relatively small compared to N verbs, we can check if the verb ends with any known ending.
   - _Alternative_: A Trie/DAWG of endings could allow O(L) lookup where L is word length. For now, a simple iteration or hash check of reasonable suffix lengths is sufficient.

### 4. Classification Flow

1.  **Iterate Verbs**: For each verb in the corpus:
2.  **Primary Lookup**: Pick a primary form (e.g., `present`).
    - Query `PatternRegistry.get_candidates(verb.present, "present")`.
    - This returns a subset of patterns that _definitely_ match the ending of the present form.
3.  **Cross-Check (Optional)**: If other forms are available (e.g., `imperfective`), get candidates for those and intersect the sets to prune further.
4.  **Full Verification**: For the surviving candidates, run the detailed `Stem Final` check and full `Strict/Loose` matching logic.
