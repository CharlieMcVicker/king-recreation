---
id: doc-1
title: Backlog Documentation Standards
type: guide
created_date: '2026-06-10 16:00'
updated_date: '2026-06-10 16:05'
---
# Backlog Documentation Standards

This document defines the architectural standards, formatting rules, and style guidelines for writing and organizing **Backlog Docs** in this project. All documentation migrations and new documents must adhere to these standards to ensure consistency, clarity, and ease of discovery.

---

## 1. Document Architecture & Namespaces

We organize backlog documents under the following path namespaces in `.backlog/docs/`:

| Namespace | Category | Purpose | Example Path |
| :--- | :--- | :--- | :--- |
| `specs/` | Specifications | Technical, structural, and algorithmic rules. | `specs/reconstruction` |
| `policies/` | Policies | Conceptual rules and conventions governing data. | `policies/blank-forms` |
| `investigations/` | Investigations | Post-mortems, root-cause analyses of issues. | `investigations/short-stems` |
| `guides/` | Guides | Explanatory guides, stack summaries, and UX walks. | `guides/tex-pipeline` |
| `plans/` | Plans | Phased project scopes and integration roadmaps. | `plans/aspect-class-companion` |

---

## 2. Structural & Formatting Standards

### A. Atomic and Bite-Sized
- Documents should be highly focused, covering a single concept, module, or sub-system.
- Avoid multi-topic or monolithic documentation. Break complex topics into smaller sub-documents and link them together.
- Use concise bullet points and direct formatting to prevent visual clutter and reduce context-retrieval token load.

### B. Header Hierarchy
- Each document must contain exactly one `<h1>` header corresponding to the title.
- Organize sub-sections with standard Markdown headings hierarchy (`##`, `###`, `####`).

---

## 3. Reference and Linking Conventions

### A. Cross-Document Referencing
- Link related backlog documents using their Backlog ID: `[Document Title](doc-ID)`.
- Example: `See the [Vacuous Matching Policy](doc-2) for details on blank form handling.`

### B. Source Code Referencing
- Reference source code files using the `file://` scheme with absolute paths: `[basename](file:///absolute/path/to/file)`.
- For specific logic, include line numbers: `[derive_stems.py:L12-30](file:///absolute/path/to/king-recreation/morphology/derive_stems.py#L12-L30)`.

---

## 4. Code Verification & Anti-Staleness Protocol ("Ember First")

To prevent outdated documentation and verify assumptions against the active codebase:
1. **Verify Accuracy**: For every document read or reviewed, verify its accuracy against the active codebase. Use `ember find "<concept_or_function>"` to locate relevant code and `ember cat <chunk_id>` (or direct file inspection) to verify implementation details.
2. **Assess Staleness & Recency**: Check when the document was last updated relative to the files it describes. If the document describes deprecated logic, dead APIs, or abandoned prototypes, classify it as stale.
3. **Do Not Migrate Stale Data**: Stale documentation or data must **not** be migrated to backlog docs. Discard stale files, or document the deprecation explicitly if the history is valuable (as a record, not as active documentation).
4. **Align Text**: If the document is mostly current but contains minor deviations from the codebase:
   - If the code is correct, update the document text to match.
   - If the code is buggy or incomplete, file a task in the backlog (e.g., `backlog task create`).
