---
id: doc-9
title: Root Dictionary View Guide
type: guide
created_date: '2026-06-10 16:18'
---# Root Dictionary View Guide

This guide describes the UI design, component layout, and grouping logic of the Root Dictionary web interface, which is used for viewing extracted roots and the lexical verbs derived from them.

---

## 1. Grouping Logic

- **Primary Grouping**: Verbs are grouped by `h_grade_root`.
- **Secondary Splitting**: If all verbs for a given `h_grade_root` share the same `glottal_grade_root`, they are displayed together. If there are multiple `glottal_grade_root` values, the group is split into separate sections for each glottal grade.
- **Header**: Display the `h-grade` and `glottal-grade` roots at the top of the group.

---

## 2. Features & UI Components

### A. Pronoun Set Color Coding
Using pronominal set determination, forms are color-coded by the pronoun set they use:
- **Set A**: Red
- **Set B**: Blue
- **3rd Person Object**: Pink/Purple
- **Pills**: Usage tags in the verb entry also use this scheme.

### B. Subvariant Filtering
- **Parsing**: `ReconstructableVerb` class names are parsed to extract the macro name and subvariant modifiers (e.g., `[perf2-inf2]`).
- **Dropdown Filter**: Integrated into [RootDetailContent.tsx](../../../../root-based-dict/src/components/roots/RootDetailContent.tsx). A dropdown allows filtering verbs by their "endings" (subvariant). Selecting an option renders only the verbs that use that specific ending configuration.

### C. Corpus Form Table
- **Component**: [CorpusTable.tsx](../../../../root-based-dict/src/components/roots/CorpusTable.tsx).
- **Tagging**: Variants are tagged on specific cells in the corpus form table (e.g., `perf2` tags the Perfective cell).
- **Forms**: Corpus forms are matched from [cherokee_nation_dictionary.csv](../../../../data/cherokee_nation_dictionary.csv).

---

## 3. Implementation Files

### Data Layer
- [data.ts](../../../../root-based-dict/src/lib/data.ts) & [data-shared.ts](../../../../root-based-dict/src/lib/data-shared.ts): Handles `getRoots()` grouping logic, pronoun set name retrieval, and variant ending resolution.

### UI Components
- [RootDetailContent.tsx](../../../../root-based-dict/src/components/roots/RootDetailContent.tsx): Client component handling filtering and view dispatch.
- [RootClassEntry.tsx](../../../../root-based-dict/src/components/roots/RootClassEntry.tsx): Displays verbs grouped by class/subclass.
- [CorpusTable.tsx](../../../../root-based-dict/src/components/roots/CorpusTable.tsx): Table with pronoun color coding and suffix tag highlights.
