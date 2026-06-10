---
id: doc-18
title: Unified Lexical Dashboard Guide
type: guide
created_date: '2026-06-10 16:47'
---# Unified Lexical Dashboard Guide

## Objective
Provide full context for a single word (`corpus_id`) by displaying its available derivation selections, root ID overrides, and suffix connections on one unified screen. This contextual view aids in complex data-entry decisions by presenting all linked metrics for a lemma simultaneously.

## Background
The user frequently references multiple pieces of data to make a single decision:
- Which canonical reconstruction is correct?
- What `root_id` should encompass this corpus ID?
- What derivational connections exist for this word?

By bringing these editable state streams into a single route or extended view, the reviewer minimizes context switching.

## Implemented Features & Routing

### 1. Unified Route
- The Next.js route is implemented in [page.tsx](../../../../root-based-dict/src/app/lexical-review/[corpusId]/page.tsx).
- Displays the selected and available root derivations as a "Hero" section using [LexicalHero.tsx](../../../../root-based-dict/src/components/LexicalHero.tsx).

### 2. Root Assignment Component
- Identifies the current `root_id` for the focused corpus item.
- Supports inline editing (hitting `Enter` saves the new `root_id` to the server).
- **Contextual Search:** If the user types a new `root_id`, the UI displays all other corpus IDs currently assigned to that `root_id` to prevent accidental orphans or merges.

### 3. Derivations Component
- Implemented in [DerivationsPanel.tsx](../../../../root-based-dict/src/components/DerivationsPanel.tsx).
- Lists any rows from `derivational_suffix_connections.csv` where the focused `corpus_id` appears in either `from_corpus_ids` or `to_corpus_ids`.
- The display is compact, showing the directional relationship ("Derived From: [Root X]" or "Derived Into: [Root Y]") with a quick toggle/checkbox for `user_approved`.

### 4. API Layer
- Uses the same `/api/curated/*` Next.js endpoints (such as `/api/curated/root-ids` and `/api/curated/derivational-connections`) to ensure immediate reactivity.
