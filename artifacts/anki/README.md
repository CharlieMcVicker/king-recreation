# Cherokee Anki Flashcards

Generated from Duane King's 1975 Cherokee Aspect Classification and the Cherokee-English Dictionary corpus.

## Quick Start (Drag & Drop .apkg Packages)

The generated `.apkg` files are ready-to-use packages that can be directly opened or dragged into Anki.
They automatically configure the **Cherokee Aspect Card (Reversible)** note type, styling, fonts, card templates, and explicit card sequencing.

- **`mascots_and_roots.apkg` (Recommended Main Deck)**: Contains Type 1 (Mascots) and Type 2 (Roots) in interleaved order.
- **`practice.apkg` (Full Practice Testing Deck)**: Contains all Type 3 conjugation practice cards for member verbs.
- **`practice_sampled.apkg` (Sampled Practice Deck)**: Contains 1-2 curated active practice cards per verb.
- **`all_cards_interleaved.apkg` (Single Unified Deck)**: Single unified deck containing mascots, roots, and practice cards spaced with a lag buffer.
- **`mascots.apkg` & `roots.apkg`**: Standalone deck packages for mascot tenses or verb roots only.

## Reversible (Double-Sided) Card Design

All decks use a **reversible note model** that generates two cards per note:
1. **Card 1: English -> Cherokee (Recognition)**:
   - **Front**: English definition + tense/root indicator.
   - **Back**: Full colored Cherokee surface form / root + full paradigm table.
2. **Card 2: Cherokee -> English (Production / Recall)**:
   - **Front**: Cherokee surface form / root (with color-coded pronoun prefix and aspect ending).
   - **Back**: English definition + tense/root indicator + full paradigm table.

### Explicit Card Ordering (`due` sequence)
Each note has its `due` queue position explicitly assigned to match the optimal spaced-interleaving sequence (`SequenceOrder`):
- When "Bury new siblings until next day" is active in Anki deck options (default), you learn the forward card on Day 1 and its reverse sibling on Day 2.
- When "Bury new siblings" is disabled, sibling cards appear in sequence order.

## CSV Import Instructions (Manual Setup)

If importing via CSV files (`.csv`), follow these steps in Anki:

1. Open Anki and click **Import File**.
2. Select `mascots_and_roots.csv` (or any other `.csv`).
3. Set **Type**: Create a Note Type named `Cherokee Aspect Card (Reversible)` with these 12 fields:
   - `Id`
   - `CardType`
   - `Deck`
   - `SequenceOrder`
   - `Class`
   - `VerbId`
   - `Definition`
   - `Root`
   - `Tense`
   - `Front`
   - `Back`
   - `ExtraInfo`
   *(Map CSV column `Tags` to the note's Tags)*
4. Ensure **Allow HTML in fields** is checked.
5. In Note Type **Cards...** settings:
   - **Card 1 (English -> Cherokee)**:
     - Front Template: `card1_front.html` (or `front_template.html`)
     - Back Template: `card1_back.html` (or `back_template.html`)
   - **Card 2 (Cherokee -> English)**:
     - Front Template: `card2_front.html`
     - Back Template: `card2_back.html`
   - **Styling**: `styling.css`
6. Set **Deck**: Select `Cherokee Roots::Roots & Mascots`.
