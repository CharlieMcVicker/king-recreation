---
id: doc-17
title: Derivational Connections Editor Guide
type: guide
created_date: '2026-06-10 16:47'
---# Derivational Connections Editor Guide

## Objective
Create a standalone sequential review interface for approving heuristic-generated derivational relationships in `curated/derivational_suffix_connections.csv`.

## Background
The `derivational_suffix_connections.csv` file is an auto-generated list of potential connections between a "base" root and a "derived" root. Humans review these proposals and mark valid ones by setting `user_approved = "x"`. Creating brand new manual connections is not supported or required from the UI; the focus is solely on triaging the pipeline proposals.

## Implemented Features & Routing

### 1. Route & Layout
- The route is defined in [page.tsx](../../../../root-based-dict/src/app/review-derivations/page.tsx) and uses the client component [ReviewDerivations.tsx](../../../../root-based-dict/src/components/ReviewDerivations.tsx).
- Provides a header for navigation containing:
  - Total connections progress (e.g., `12 / 105 connections reviewed`).
  - Next/Prev buttons (supporting `Left`/`Right` arrow keyboard shortcuts).
  - A toggle switch: **"Unreviewed Only"** vs **"Show All"** (defaulting to "Unreviewed Only"). An item is Unreviewed if `user_approved` is blank.

### 2. The Data Display
The UI presents the two sides of the connection side-by-side:
- **Left Column ("From"):** Displays `from_root_id`, `from_h_grade`, `from_g_grade`, `from_class`, and `from_stem_type`, along with English definitions mapped to the `from_corpus_ids`.
- **Right Column ("To"):** Displays `to_root_id`, `to_h_grade`, `to_g_grade`, `to_class`, and `to_stem_type`, along with English definitions mapped to `to_corpus_ids`.
- **Highlighting Differences:** Visually highlights the fields that differ between the left and right sides (such as class or stem type differences).

### 3. Primary Action
- A prominent toggle/checkbox to mark the connection as **Approved**.
- Hitting `Enter` toggles the approval state and automatically advances to the next connection.

### 4. Backend Integration
- The API endpoint [route.ts](../../../../root-based-dict/src/app/api/curated/derivational-connections/route.ts) handles POST requests.
- It matches the connection using the unique composite key (the 8-tuple of from/to root and class data), toggles `user_approved` to `"x"`, and rewrites `curated/derivational_suffix_connections.csv` with a stable sort order.
