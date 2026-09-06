# Cherokee Anki Flashcards

Generated from Duane King's 1975 Cherokee Aspect Classification and the Cherokee-English Dictionary corpus.

## Quick Start (Drag & Drop .apkg Packages)

The generated `.apkg` files are ready-to-use packages that can be directly opened or dragged into Anki.
They automatically configure the note types, styling, fonts, card templates, media audio, and sequencing.

### Verb Aspect Inflection & Root Decks (`Cherokee Aspect Card (Reversible)`)
- **`mascots_and_roots.apkg` (Recommended Main Deck)**: Contains Type 1 (Mascots) and Type 2 (Roots) in interleaved order.
- **`practice.apkg` (Full Practice Testing Deck)**: Contains all Type 3 conjugation practice cards for member verbs.
- **`practice_sampled.apkg` (Sampled Practice Deck)**: Contains 1-2 curated active practice cards per verb.
- **`all_cards_interleaved.apkg` (Single Unified Deck)**: Single unified deck containing mascots, roots, and practice cards spaced with a lag buffer.
- **`mascots.apkg` & `roots.apkg`**: Standalone deck packages for mascot tenses or verb roots only.

### Cherokee Sentence Cloze Deck (`Cherokee Sentence Cloze`)
- **`cloze_sentences.apkg` (Sentence Cloze Deck)**: 7,200+ fill-in-the-blank cards generated from all 1,862 dictionary example sentences in `audiodownload/officialdata.csv`. Deck name is **`Cherokee Cloze Sentences`**. Each card blanks out one word of the Cherokee sentence (in both Syllabary and clean Phonetics), displays the full English translation on the front for meaning context, and reveals the target word answer below the sentence along with natural sentence audio on the back!
- **`cloze_sentences.csv`**: Raw CSV data with all 15 fields for manual Anki import or external analysis.

## Reversible Aspect Card Design

Aspect decks use a **reversible note model** that generates two cards per note:
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

## Sentence Cloze Card Design

The Sentence Cloze deck uses the **`Cherokee Sentence Cloze`** note model with deck name **`Cherokee Cloze Sentences`**:
1. **Card Front**:
   - **Syllabary**: Sentence with target word replaced by a highlighted blank (`[ ______ ]`)
   - **Clean Phonetics**: Sentence with target word replaced by a highlighted blank (`[ ______ ]`) (tones and length colons removed for clean reading)
   - **English Translation**: Complete English sentence for semantic context
2. **Card Back**:
   - **Full Syllabary**: Sentence with target word highlighted in green
   - **Full Clean Phonetics**: Sentence with target word highlighted in green
   - **English Translation**: Complete English sentence
   - **Divider & Answer Box**: Target missing word shown prominently below the sentence in Syllabary and Phonetics
   - **Sentence Audio**: Natural sentence pronunciation recording played automatically


## Audio & Example Sentences

### 1. Cherokee Word Pronunciations
Word audio recordings from the Cherokee Nation App Dictionary have been integrated onto the Cherokee side of aspect cards where recordings are available:
- **Card 1: English -> Cherokee (Recognition)**: Word audio plays automatically when revealing the Cherokee back side / answer.
- **Card 2: Cherokee -> English (Production / Recall)**: Word audio plays automatically when the Cherokee front side / prompt is displayed.

### 2. Natural Example Sentences with Audio Listen Buttons & Class Mascot Anchors
Each verb's **Extra Info** section includes natural example sentences from the Cherokee Nation Dictionary:
- **Phonetics & Tone**: Formatted first with full tone markers.
- **Cherokee Syllabary**: Bolded target verb with an **inline audio play button** `[sound:Sentence_for_entry_XXXX.m4a]`.
- **English Translation**: Complete contextual translation.
- **Class Mascot Anchors**: For member verbs (roots and practice cards), the header displays the Class Mascot root, 3rd person present form, and English definition.
- Available for **594 out of 595 verbs** (99.8% coverage).
- All referenced word audio and sentence audio files are packaged directly into the `.apkg` files.

## CSV Import Instructions (Manual Setup)

### Importing Aspect Cards
If importing `mascots_and_roots.csv` (or any aspect `.csv`):
1. Open Anki and click **Import File**.
2. Select `mascots_and_roots.csv`.
3. Set **Type**: Create a Note Type named `Cherokee Aspect Card (Reversible)` with these 12 fields:
   - `Id`, `CardType`, `Deck`, `SequenceOrder`, `Class`, `VerbId`, `Definition`, `Root`, `Tense`, `Front`, `Back`, `ExtraInfo` *(Map `Tags` to note tags)*
4. In Note Type **Cards...** settings:
   - **Card 1 (English -> Cherokee)**: Front: `card1_front.html`, Back: `card1_back.html`
   - **Card 2 (Cherokee -> English)**: Front: `card2_front.html`, Back: `card2_back.html`
   - **Styling**: `styling.css`

### Importing Sentence Cloze Cards
If importing `cloze_sentences.csv`:
1. Open Anki and click **Import File**.
2. Select `cloze_sentences.csv`.
3. Set **Type**: Create a Note Type named `Cherokee Sentence Cloze` with these 15 fields:
   - `Id`, `Deck`, `SequenceOrder`, `EntryNo`, `WordIndex`, `TotalWords`, `English`, `FrontSyllabary`, `FrontPhonetics`, `TargetWordSyllabary`, `TargetWordPhonetics`, `BackSyllabary`, `BackPhonetics`, `Audio`, `Tags`
4. In Note Type **Cards...** settings:
   - **Front Template**: `cloze_front.html`
   - **Back Template**: `cloze_back.html`
   - **Styling**: `styling.css`
5. Ensure **Allow HTML in fields** is checked.
