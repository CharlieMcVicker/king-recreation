"""
Anki Flashcard Generator for Cherokee Root Dictionary.
Loads reconstructed verbs, resolves mascots, generates cards, and exports CSVs.
"""

from __future__ import annotations

import csv
import hashlib
import os
import random
import tempfile
from collections import Counter
from typing import Any

import genanki

from anki.english_inflector import (
    clean_pronouns,
    inflect_english_definition,
)
from anki.formatter import (
    FORM_LABELS,
    FORM_MAP,
    build_card_back_html,
    build_card_front_html,
    build_verb_table_html,
)
from anki.models import AnkiCard
from anki.sequencer import AnkiSequencer
from dictionary_pipeline.dictionary_forms import DictionaryVerb
from dictionary_pipeline.orthography import unrespell_consonants
from dictionary_pipeline.paths import ARTIFACTS_DIR
from tex_dictionary.companion_data import (
    AspectClass,
    load_aspect_classes,
)
from tex_dictionary.mascot_resolver import MascotResolver

ANKI_OUTPUT_DIR = os.path.join(ARTIFACTS_DIR, "anki")
CHEROKEE_MODEL_ID = 1607392319
CHEROKEE_MODEL_NAME = "Cherokee Aspect Card (Reversible)"


def make_anki_id(name: str) -> int:
    """Generates a deterministic 31-bit integer for Anki deck or model IDs."""
    return int(hashlib.md5(name.encode("utf-8")).hexdigest()[:8], 16) & 0x7FFFFFFF


def get_anki_css_content() -> str:
    """Returns CSS styles for Cherokee flashcards."""
    return """/* Cherokee Anki Card Styles */
@font-face {
    font-family: 'Noto Sans Cherokee';
    src: url('_NotoSansCherokee-Regular.ttf');
}

.card {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans Cherokee", Helvetica, Arial, sans-serif;
    font-size: 16px;
    text-align: center;
    color: #1a202c;
    background-color: #ffffff;
    line-height: 1.5;
    padding: 16px;
}

.card-front, .card-back {
    max-width: 600px;
    margin: 0 auto;
}

.cherokee-word {
    font-size: 1.8em;
    font-weight: 500;
    margin-bottom: 8px;
    color: #ff8888;
}

.pron-set-a {
    color: #c53030;
    font-weight: 600;
}

.pron-set-b {
    color: #8888ff;
    font-weight: 600;
}

.pron-person-to-person {
    color: #6b46c1;
    font-weight: 600;
}

.aspect-suffix {
    font-weight: bold;
    border-bottom: 2px solid #888888;
    color: #cc5555;
}

.class-card-header {
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    padding: 12px;
    margin-top: 12px;
    text-align: left;
}

hr#answer {
    border: 0;
    height: 1px;
    background: #e2e8f0;
    margin: 20px 0;
}
"""


def get_cherokee_model() -> genanki.Model:
    """Creates the reversible Cherokee aspect model with 2 card templates."""
    css_content = get_anki_css_content()
    return genanki.Model(
        CHEROKEE_MODEL_ID,
        CHEROKEE_MODEL_NAME,
        fields=[
            {"name": "Id"},
            {"name": "CardType"},
            {"name": "Deck"},
            {"name": "SequenceOrder"},
            {"name": "Class"},
            {"name": "VerbId"},
            {"name": "Definition"},
            {"name": "Root"},
            {"name": "Tense"},
            {"name": "Front"},
            {"name": "Back"},
            {"name": "ExtraInfo"},
        ],
        templates=[
            {
                "name": "Card 1: English -> Cherokee",
                "qfmt": "{{Front}}",
                "afmt": "{{Front}}\n\n<hr id=\"answer\">\n\n{{Back}}\n\n{{ExtraInfo}}",
            },
            {
                "name": "Card 2: Cherokee -> English",
                "qfmt": "{{Back}}",
                "afmt": "{{Back}}\n\n<hr id=\"answer\">\n\n{{Front}}\n\n{{ExtraInfo}}",
            },
        ],
        css=css_content,
    )


def get_anki_media_files() -> list[str]:
    """Finds and prepares Cherokee font files for Anki package embedding."""
    font_path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "Noto_Sans_Cherokee",
            "static",
            "NotoSansCherokee-Regular.ttf",
        )
    )
    if os.path.exists(font_path):
        tmp_font = os.path.join(
            tempfile.gettempdir(), "_NotoSansCherokee-Regular.ttf"
        )
        with open(font_path, "rb") as f_in, open(tmp_font, "wb") as f_out:
            f_out.write(f_in.read())
        return [tmp_font]
    return []


def write_csv(filepath: str, cards: list[AnkiCard]) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=AnkiCard.get_csv_fieldnames())
        writer.writeheader()
        for card in cards:
            writer.writerow(card.to_csv_row())
    print(f"Exported {len(cards)} cards to {filepath}")


def write_apkg(
    filepath: str,
    deck_name: str,
    cards: list[AnkiCard],
    model: genanki.Model | None = None,
    media_files: list[str] | None = None,
) -> None:
    """Exports cards to an Anki .apkg package file."""
    if model is None:
        model = get_cherokee_model()
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    deck_id = make_anki_id(deck_name)
    deck = genanki.Deck(deck_id, deck_name)
    for card in cards:
        note = card.to_genanki_note(model)
        deck.add_note(note)
    pkg = genanki.Package(deck)
    if media_files:
        pkg.media_files = media_files
    pkg.write_to_file(filepath)
    print(
        f"Exported {len(cards)} notes ({len(cards)*2} reversible cards) to"
        f" {filepath}"
    )


def generate_anki_cards(
    initial_batch_size: int = 5,
    interleave_batch_size: int = 3,
    practice_lag_cards: int = 25,
    sample_practice_min: int = 1,
    sample_practice_max: int = 2,
    filter_tag: str = "filtered",
    seed: int = 42,
) -> dict[str, list[AnkiCard]]:
    """
    Generates all 3 types of cards and exports CSVs and HTML templates.
    Classes are ordered by their total verb count (main class + [~~~] subclasses),
    with all subclasses placed immediately after their main class.
    """
    print("Initializing MascotResolver and loading aspect classes...")
    resolver = MascotResolver()
    aspect_classes = load_aspect_classes()
    class_lookup: dict[str, AspectClass] = {
        c.full_name: c for c in aspect_classes
    }

    # Group all verbs by their exact class_name (e.g. 'ih-ohd', 'ih-ohd[perf2]')
    class_groups: dict[str, list[DictionaryVerb]] = {}
    for v in resolver.all_verbs:
        c_name = v.morphology.class_name
        class_groups.setdefault(c_name, []).append(v)

    # Group by base class (e.g. 'ih-ohd' covers 'ih-ohd', 'ih-ohd[perf2]', etc.)
    base_groups: dict[str, list[str]] = {}
    for c_name in class_groups.keys():
        base = c_name.split("[")[0]
        base_groups.setdefault(base, []).append(c_name)

    # Sort base groups descending by total verbs across main class and all its subclasses
    sorted_bases = sorted(
        base_groups.keys(),
        key=lambda b: sum(len(class_groups[sub]) for sub in base_groups[b]),
        reverse=True,
    )

    # Build ordered list of classes: main class first, then its [~~~] subclasses right after
    ordered_class_names: list[str] = []
    class_mascots: dict[str, DictionaryVerb] = {}
    class_member_verbs: dict[str, list[DictionaryVerb]] = {}

    for base in sorted_bases:
        sub_names = base_groups[base]
        # Main unbracketed class first, then subclasses sorted by verb count descending
        sorted_subs = sorted(
            sub_names,
            key=lambda name: (name != base, -len(class_groups[name]), name),
        )

        for c_name in sorted_subs:
            g_verbs = class_groups.get(c_name, [])
            if not g_verbs:
                continue

            variants = sorted(
                list(set(resolver.get_variant_label(v) for v in g_verbs))
            )
            variant = "Plain" if "Plain" in variants else variants[0]
            mascot_verb = resolver.resolve_mascot(c_name, variant)

            if not mascot_verb:
                g_with_cid = [v for v in g_verbs if v.corpus_id]
                if g_with_cid:
                    mascot_verb = sorted(
                        g_with_cid, key=lambda v: v.definition.lower()
                    )[0]
                else:
                    mascot_verb = sorted(
                        g_verbs, key=lambda v: v.definition.lower()
                    )[0]

            class_mascots[c_name] = mascot_verb

            # Member verbs (excluding the mascot verb)
            mascot_cid = mascot_verb.corpus_id
            member_verbs = [
                v
                for v in g_verbs
                if not (
                    v.corpus_id == mascot_cid
                    and v.definition == mascot_verb.definition
                )
            ]
            # Sort member verbs deterministically
            member_verbs.sort(
                key=lambda v: (
                    v.corpus_id if v.corpus_id is not None else 999999,
                    v.morphology.h_grade_root,
                    v.definition,
                )
            )
            class_member_verbs[c_name] = member_verbs
            ordered_class_names.append(c_name)

    # 2. Build Card Objects
    mascot_cards_by_class: dict[str, list[AnkiCard]] = {}
    root_cards_by_verb_id: dict[str, AnkiCard] = {}
    practice_cards_by_verb_id: dict[str, list[AnkiCard]] = {}

    deck_main = "Cherokee::Roots & Mascots"
    deck_practice = "Cherokee::Practice"

    # Build Type 1: Mascot Tense Cards
    for c_name in ordered_class_names:
        mascot_verb = class_mascots[c_name]
        cards: list[AnkiCard] = []
        cls_meta = class_lookup.get(c_name) or class_lookup.get(
            c_name.split("[")[0]
        )
        mascot_extra_table = build_verb_table_html(
            c_name, mascot_verb, is_mascot=True, aspect_class=cls_meta
        )
        cid_str = str(mascot_verb.corpus_id or mascot_verb.definition)

        for fn, eng_tense, syl_header in FORM_LABELS:
            seg = mascot_verb.segmented_forms.get(fn)
            if not seg or seg == "---":
                continue

            card_id = f"mascot_{c_name}_{fn}_{cid_str}"
            m_def = inflect_english_definition(mascot_verb.definition, fn)
            front = build_card_front_html(
                card_type="mascot_tense",
                definition=m_def,
                tense_name=eng_tense,
                syllabary_header=syl_header,
                class_name=c_name,
            )
            back = build_card_back_html(
                card_type="mascot_tense",
                verb=mascot_verb,
                form_name=fn,
                segmented_form=seg,
            )
            tags = [
                "cherokee",
                f"class::{c_name}",
                "type::mascot_tense",
                f"tense::{fn}",
            ]

            card = AnkiCard(
                card_id=card_id,
                card_type="mascot_tense",
                deck=deck_main,
                sequence_order=0,
                class_name=c_name,
                verb_id=cid_str,
                definition=m_def,
                root=mascot_verb.morphology.h_grade_root,
                tense=eng_tense,
                front=front,
                back=back,
                extra_info=mascot_extra_table,
                tags=tags,
            )
            cards.append(card)

        mascot_cards_by_class[c_name] = cards

    # Build Type 2 (Root) & Type 3 (Practice) Cards for all member verbs
    for c_name in ordered_class_names:
        member_verbs = class_member_verbs[c_name]
        cls_meta = class_lookup.get(c_name) or class_lookup.get(
            c_name.split("[")[0]
        )

        for v in member_verbs:
            vid = str(v.corpus_id or v.definition)
            root_str = v.morphology.h_grade_root
            if (
                v.morphology.glottal_grade_root
                and v.morphology.glottal_grade_root != v.morphology.h_grade_root
            ):
                root_str += f" / {v.morphology.glottal_grade_root}"
            comm_root = unrespell_consonants(root_str)

            # Extra info for this specific member verb
            verb_extra_table = build_verb_table_html(
                c_name, v, is_mascot=False, aspect_class=cls_meta
            )

            # Type 2: Verb Root Card
            root_card_id = f"root_{c_name}_{vid}"
            r_def = clean_pronouns(v.definition, "3rd_she")
            r_front = build_card_front_html(
                card_type="verb_root",
                definition=r_def,
                class_name=c_name,
            )
            r_back = build_card_back_html(
                card_type="verb_root",
                verb=v,
            )
            r_tags = [
                "cherokee",
                f"class::{c_name}",
                "type::verb_root",
            ]
            root_card = AnkiCard(
                card_id=root_card_id,
                card_type="verb_root",
                deck=deck_main,
                sequence_order=0,
                class_name=c_name,
                verb_id=vid,
                definition=r_def,
                root=comm_root,
                tense="",
                front=r_front,
                back=r_back,
                extra_info=verb_extra_table,
                tags=r_tags,
            )
            root_cards_by_verb_id[vid] = root_card

            # Type 3: Practice Test Cards for all available forms
            p_cards: list[AnkiCard] = []
            for fn, eng_tense, syl_header in FORM_LABELS:
                seg = v.segmented_forms.get(fn)
                if not seg or seg == "---":
                    continue

                p_card_id = f"practice_{c_name}_{fn}_{vid}"
                p_def = inflect_english_definition(v.definition, fn)
                p_front = build_card_front_html(
                    card_type="practice_test",
                    definition=p_def,
                    tense_name=eng_tense,
                    syllabary_header=syl_header,
                    class_name=c_name,
                )
                p_back = build_card_back_html(
                    card_type="practice_test",
                    verb=v,
                    form_name=fn,
                    segmented_form=seg,
                )
                p_tags = [
                    "cherokee",
                    f"class::{c_name}",
                    "type::practice_test",
                    f"tense::{fn}",
                ]
                practice_card = AnkiCard(
                    card_id=p_card_id,
                    card_type="practice_test",
                    deck=deck_practice,
                    sequence_order=0,
                    class_name=c_name,
                    verb_id=vid,
                    definition=p_def,
                    root=comm_root,
                    tense=eng_tense,
                    front=p_front,
                    back=p_back,
                    extra_info=verb_extra_table,
                    tags=p_tags,
                )
                p_cards.append(practice_card)

            # Randomly select 1-2 practice cards per verb to be active (unfiltered);
            # tag the remaining cards with filter_tag so they can be easily filtered/suspended.
            if p_cards:
                verb_rng = random.Random(f"{vid}_{seed}")
                num_to_keep = min(
                    len(p_cards),
                    verb_rng.randint(sample_practice_min, sample_practice_max),
                )
                kept_indices = set(
                    verb_rng.sample(range(len(p_cards)), num_to_keep)
                )

                for idx, p_card in enumerate(p_cards):
                    if idx not in kept_indices:
                        p_card.tags.append(filter_tag)

            practice_cards_by_verb_id[vid] = p_cards

    # 3. Run Sequencer to interleave and set order
    sequencer = AnkiSequencer(
        initial_batch_size=initial_batch_size,
        interleave_batch_size=interleave_batch_size,
        practice_lag_cards=practice_lag_cards,
    )
    all_cards, mascots_and_roots, mascots, roots, practice = (
        sequencer.sequence_cards(
            ordered_class_names=ordered_class_names,
            class_member_verbs=class_member_verbs,
            mascot_cards_by_class=mascot_cards_by_class,
            root_cards_by_verb_id=root_cards_by_verb_id,
            practice_cards_by_verb_id=practice_cards_by_verb_id,
        )
    )

    # Filtered subset: Only practice cards that DO NOT have the filter_tag
    practice_sampled = [c for c in practice if filter_tag not in c.tags]

    # 4. Export CSV & APKG Files
    os.makedirs(ANKI_OUTPUT_DIR, exist_ok=True)
    cherokee_model = get_cherokee_model()
    media_files = get_anki_media_files()

    export_targets = [
        ("all_cards_interleaved", "Cherokee::All Interleaved", all_cards),
        ("mascots_and_roots", "Cherokee::Roots & Mascots", mascots_and_roots),
        ("mascots", "Cherokee::Mascots", mascots),
        ("roots", "Cherokee::Roots", roots),
        ("practice", "Cherokee::Practice", practice),
        ("practice_sampled", "Cherokee::Practice (Sampled)", practice_sampled),
    ]

    for basename, deck_name, card_list in export_targets:
        csv_path = os.path.join(ANKI_OUTPUT_DIR, f"{basename}.csv")
        apkg_path = os.path.join(ANKI_OUTPUT_DIR, f"{basename}.apkg")
        write_csv(csv_path, card_list)
        write_apkg(
            apkg_path,
            deck_name,
            card_list,
            model=cherokee_model,
            media_files=media_files,
        )

    # 5. Export Templates & Documentation
    _export_anki_assets(ANKI_OUTPUT_DIR, filter_tag=filter_tag)

    return {
        "all_cards": all_cards,
        "mascots_and_roots": mascots_and_roots,
        "mascots": mascots,
        "roots": roots,
        "practice": practice,
        "practice_sampled": practice_sampled,
    }


def _export_anki_assets(output_dir: str, filter_tag: str = "filtered") -> None:
    """Exports Anki note type HTML templates, CSS, and documentation."""
    css_content = get_anki_css_content()
    with open(os.path.join(output_dir, "styling.css"), "w", encoding="utf-8") as f:
        f.write(css_content)

    card1_front = """{{Front}}"""
    card1_back = """{{Front}}

<hr id="answer">

{{Back}}

{{ExtraInfo}}"""

    card2_front = """{{Back}}"""
    card2_back = """{{Back}}

<hr id="answer">

{{Front}}

{{ExtraInfo}}"""

    # Export Card 1 and Card 2 templates
    with open(
        os.path.join(output_dir, "card1_front.html"), "w", encoding="utf-8"
    ) as f:
        f.write(card1_front)

    with open(
        os.path.join(output_dir, "card1_back.html"), "w", encoding="utf-8"
    ) as f:
        f.write(card1_back)

    with open(
        os.path.join(output_dir, "card2_front.html"), "w", encoding="utf-8"
    ) as f:
        f.write(card2_front)

    with open(
        os.path.join(output_dir, "card2_back.html"), "w", encoding="utf-8"
    ) as f:
        f.write(card2_back)

    # Backwards compatibility aliases
    with open(
        os.path.join(output_dir, "front_template.html"), "w", encoding="utf-8"
    ) as f:
        f.write(card1_front)

    with open(
        os.path.join(output_dir, "back_template.html"), "w", encoding="utf-8"
    ) as f:
        f.write(card1_back)

    readme_content = f"""# Cherokee Anki Flashcards

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
6. Set **Deck**: Select `Cherokee::Roots & Mascots`.
"""
    with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"Exported Anki documentation and templates to {output_dir}")
