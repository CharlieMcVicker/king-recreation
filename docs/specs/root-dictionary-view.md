# Frontend Spec: Root Dictionary View

This document describes the implementation of the "Root Dictionary" for viewing _roots_ and the lexical verbs derived from them.

## Grouping Logic

- **Primary Grouping**: Verbs are grouped by `h_grade_root`.
- **Secondary Splitting**: If all verbs for a given `h_grade_root` share the same `glottal_grade_root`, they are displayed together. If there are multiple `glottal_grade_root` values, the group is split into separate sections for each glottal grade.
- **Header**: Display the `h-grade` and `glottal-grade` roots at the top of the group.

## Features & UI Components

### 1. Pronoun Set Color Coding

Using a port of `king_recreation.phonology_data.get_pronominal_set_name` to the frontend (`lib/data-shared.ts`), forms are color-coded by the pronoun set they use.

- **Set A**: Red
- **Set B**: Blue
- **3rd Person Object**: Pink/Purple
- **Pills**: Usage tags in the verb entry also use this scheme.

### 2. Subvariant Filtering

- **Parsing**: `ReconstructableVerb` class names are parsed to extract the macro name and subvariant modifiers (e.g., `[perf2-inf2]`).
- **Component**: `SubvariantFilter` (and `RootDetailContent` logic).
- **Behavior**: A dropdown allows filtering verbs by their "endings" (subvariant). Selecting an option renders only the verbs that use that specific ending configuration.

### 3. Corpus Form Table

- **Component**: `CorpusTable`.
- **Tagging**: Variants are tagged on specific cells in the corpus form table (e.g., `perf2` tags the Perfective cell).
- **Forms**: Corpus forms are matched from `cherokee_nation_dictionary.csv`.

## Implementation Details

### Data Layer (`lib/data.ts` & `lib/data-shared.ts`)

- [x] `getRoots()`: Groups verbs by root and handles glottal grade splits.
- [x] `getPronominalSetName`: Ported logic for pronoun set determination.

### Components

- [x] `RootList` (`app/roots/page.tsx`): Dictionary overview page listing all roots.
- [x] `RootDetail` (`app/roots/[slug]/page.tsx`): Server component wrapper.
- [x] `RootDetailContent` (`components/roots/RootDetailContent.tsx`): Client component handling filtering and display.
- [x] `RootClassEntry` (`components/roots/RootClassEntry.tsx`): Displays verbs grouped by class/subclass.
- [x] `CorpusTable` (`components/roots/CorpusTable.tsx`): Table with variant tagging and pronoun color coding.

### Routing

- [x] `/roots`: Root Dictionary Index.
- [x] `/roots/[slug]`: Root Detail Page.
