Here is the finalized specification, refined with your formatting decisions and structured specifically to hand off to an agent working within your existing repo architecture.

---

# Technical Specification: Class & Mascot Verb Reference Artifact

## 1. Overview & Objective

Expand the Tech Dictionary data and PDF generation pipeline to produce a new community-facing reference document. This artifact presents each of the 50 verb paradigm classes led by a user-selected **mascot word** (showing its full 6-form reference table), followed by a multi-column list of all member verbs belonging to that class.

All printed text must be transformed into the **community-facing orthography**, including specific boundary handling logic for underlying $D + H$ sequences.

---

## 2. Mascot Selection Data Contract

Mascot selections will utilize the existing repository CSV structure rather than creating a new file format.

* **File Location / Format:** CSV tracking `class`, `subclass`, and `mascot_corpus_id`.
* **Schema:**
```csv
class,subclass,mascot_corpus_id
cause,,1042
stative,,891

```


* **Picker Integration:** The existing web application interface will consume this CSV, allowing rapid selection and updating of missing `mascot_corpus_id` entries per class/subclass row.

---

## 3. Phonology & Orthography Mapping Rules

* **Target Output:** Community-facing orthography across all PDF surface forms, templates, paradigms, and definitions.
* **Boundary Condition ($D + H$):**
* When morpheme concatenation results in a morpheme-final $D$ meeting a prefix/root-initial $H$, orthographic conversion must preserve the $D$ and $H$ sequence explicitly across the segment boundary.
* Do **not** merge or re-spell $D + H$ into aspirated $T/Th$ at boundary points; rendering relies on reader phonological competence to pronounce the sequence appropriately.



---

## 4. Document Layout & XeLaTeX Pipeline Specifications

The pipeline component will ingest class data alongside the resolved `mascot_corpus_id` mapping to generate a printable XeLaTeX source file.

### A. Class Section Header & Mascot Paradigm Table

1. **Class Title:** Display class identifier (and subclass, if applicable).
2. **Mascot Reference Table:** Render the 6 standard reference forms using the canonical ordering and labeling defined in the codebase's existing paradigm generation modules.

### B. Class Member List (Multi-Column Layout)

* **Structure:** A 3-column view (`multicol` package or equivalent).
* **Entry Block Format:** Strict **3-line vertical stack** per verb (no inline parentheses):

$$\begin{array}{l} \textbf{Line 1:} \quad \text{Surface Third-Person Present Form} \\ \textbf{Line 2:} \quad \text{Template} \\ \textbf{Line 3:} \quad \text{Definition / Gloss} \end{array}$$

* **TeX Block Mockup:**
```latex
\begin{minipage}{\linewidth}
  \raggedright
  \textbf{SurfaceForm3P} \\
  {\small \textsf{TemplateString}} \\
  {\footnotesize \textit{Definition line}}
\end{minipage}\vspace{0.4em}

```



---

## 5. Handoff Checklist for Implementation Agent

When implementing against the codebase, the execution agent should inspect and integrate with:

1. **Existing CSV Reader/Writer:** Connect the web UI to read/write `mascot_corpus_id` directly in the active mascot CSV configuration file.
2. **Orthography Converter Module:** Verify where segment boundary markers are passed to the community orthography converter so $D + H$ sequences across morpheme boundaries are correctly maintained.
3. **Canonical Reference Ordering:** Import the exact 6-form sequence array/enum used in standard dictionary entry exports to drive the mascot table generation.
4. **XeLaTeX Template Engine:** Add a target script/CLI command to the build pipeline to compile this new artifact alongside existing dictionary PDF builds.