"""
Anki Flashcard Generator for Cherokee Root Dictionary.
Loads reconstructed verbs, resolves mascots, generates cards, and exports CSVs.
"""

from __future__ import annotations

import csv
import hashlib
import os
import random
import re
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

DEFAULT_CONJUGATIONS_CSV = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "audiodownload", "conjugations.csv"
    )
)
DEFAULT_AUDIO_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "audiodownload", "audio_files"
    )
)


def load_audio_mapping(
    csv_path: str = DEFAULT_CONJUGATIONS_CSV,
    audio_dir: str = DEFAULT_AUDIO_DIR,
) -> tuple[dict[tuple[str, str], str], dict[str, str]]:
    """
    Loads word audio mappings from conjugations.csv.
    Returns:
        audio_map: dict mapping (base_entry_no, form_name) -> audio_filename
        audio_files_by_name: dict mapping audio_filename -> absolute filepath on disk
    """
    if not os.path.exists(csv_path) or not os.path.exists(audio_dir):
        return {}, {}

    audio_files_on_disk = {
        fname: os.path.join(audio_dir, fname)
        for fname in os.listdir(audio_dir)
        if os.path.isfile(os.path.join(audio_dir, fname))
    }

    audio_map: dict[tuple[str, str], str] = {}

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            audio_file = (
                row.get("cn-app-dictionary.csv_Word audio")
                or row.get("Word audio")
                or ""
            ).strip()
            form_name = (
                row.get("hierarchical-dict.json_Segmented Form")
                or row.get("Segmented Form")
                or ""
            ).strip()
            entry_no = (
                row.get("cn-app-dictionary.csv_\ufeffEntry No.")
                or row.get("cn-app-dictionary.csv_Entry No.")
                or row.get("Entry No.")
                or ""
            ).strip()

            if audio_file and form_name and entry_no:
                if audio_file in audio_files_on_disk:
                    base_eno = entry_no.split(".")[0]
                    audio_map[(base_eno, form_name)] = audio_file

    return audio_map, audio_files_on_disk


DEFAULT_OFFICIAL_DATA_CSV = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "audiodownload", "officialdata.csv"
    )
)
DEFAULT_SENTENCE_AUDIO_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), "..", "..", "audiodownload", "sentence_audio"
    )
)


def load_sentence_mapping(
    csv_path: str = DEFAULT_OFFICIAL_DATA_CSV,
    audio_dir: str = DEFAULT_SENTENCE_AUDIO_DIR,
) -> tuple[dict[str, dict[str, str]], dict[str, str]]:
    """
    Loads example sentences and sentence audio mappings from officialdata.csv.
    Returns:
        sentences_by_entry: dict mapping base_entry_no -> {"phon": ..., "syll": ..., "engl": ..., "audio": ...}
        sentence_audio_files_by_name: dict mapping audio_filename -> absolute filepath on disk
    """
    if not os.path.exists(csv_path):
        return {}, {}

    audio_files_on_disk = {}
    if os.path.exists(audio_dir):
        for fname in os.listdir(audio_dir):
            full_p = os.path.join(audio_dir, fname)
            if os.path.isfile(full_p):
                audio_files_on_disk[fname] = full_p

    sentences_by_entry: dict[str, dict[str, str]] = {}

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for row in reader:
            eno = (
                row.get("Entry No.")
                or row.get("\ufeffEntry No.")
                or row.get("No.")
                or ""
            ).strip()
            if not eno:
                continue
            base_eno = eno.split(".")[0]
            if base_eno in sentences_by_entry:
                continue  # Keep the primary (first) example sentence

            s_syll = row.get("Sentence-1 SYLL", "").strip()
            s_phon = row.get("Sentence-1 PHON", "").strip()
            s_engl = row.get("Sentence-1 ENGL", "").strip()
            s_audio = row.get("Sentence 1 audio", "").strip()

            if s_syll or s_phon or s_engl:
                audio_valid = s_audio if s_audio in audio_files_on_disk else ""
                sentences_by_entry[base_eno] = {
                    "syll": s_syll,
                    "phon": s_phon,
                    "engl": s_engl,
                    "audio": audio_valid,
                }

    return sentences_by_entry, audio_files_on_disk


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

/* Cloze Fill-in-the-Blank Styles */
.cloze-container {
    max-width: 620px;
    margin: 0 auto;
    text-align: center;
}

.cloze-sentence-syll {
    font-family: 'Noto Sans Cherokee', sans-serif;
    font-size: 1.8em;
    line-height: 1.6;
    color: #1a202c;
    margin-bottom: 12px;
}

.cloze-sentence-phon {
    font-size: 1.25em;
    color: #4a5568;
    line-height: 1.5;
    margin-bottom: 16px;
}

.cloze-blank {
    display: inline-block;
    background-color: #fef3c7;
    border-bottom: 3px solid #d97706;
    color: #92400e;
    font-weight: bold;
    padding: 0 8px;
    border-radius: 4px;
    min-width: 50px;
}

.cloze-target {
    display: inline-block;
    background-color: #d1fae5;
    border-bottom: 3px solid #059669;
    color: #065f46;
    font-weight: bold;
    padding: 0 6px;
    border-radius: 4px;
}

.cloze-english {
    font-size: 1.15em;
    color: #2b6cb0;
    font-weight: 500;
    margin-top: 14px;
    padding-top: 12px;
    border-top: 1px dashed #e2e8f0;
}

.cloze-answer-box {
    background: #f7fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 14px 16px;
    margin: 12px 0 16px 0;
    text-align: center;
}

.cloze-answer-label {
    font-size: 0.8em;
    color: #718096;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 4px;
}

.cloze-answer-syll {
    font-family: 'Noto Sans Cherokee', sans-serif;
    font-size: 2.1em;
    font-weight: bold;
    color: #2c5282;
    margin-bottom: 2px;
}

.cloze-answer-phon {
    font-size: 1.25em;
    color: #4a5568;
    font-weight: 500;
}

.cloze-audio-container {
    margin-top: 14px;
}

/* ==========================================================================
   Dark Mode / Night Mode Support for Anki
   ========================================================================== */
.nightMode.card,
.night_mode .card,
body.nightMode .card,
body.night_mode .card {
    background-color: #20262e;
    color: #e2e8f0;
}

.nightMode .cloze-sentence-syll,
.night_mode .cloze-sentence-syll,
body.nightMode .cloze-sentence-syll,
body.night_mode .cloze-sentence-syll {
    color: #f7fafc;
}

.nightMode .cloze-sentence-phon,
.night_mode .cloze-sentence-phon,
body.nightMode .cloze-sentence-phon,
body.night_mode .cloze-sentence-phon {
    color: #cbd5e0;
}

.nightMode .cloze-blank,
.night_mode .cloze-blank,
body.nightMode .cloze-blank,
body.night_mode .cloze-blank {
    background-color: #78350f;
    border-bottom: 3px solid #f59e0b;
    color: #fef3c7;
}

.nightMode .cloze-target,
.night_mode .cloze-target,
body.nightMode .cloze-target,
body.night_mode .cloze-target {
    background-color: #064e3b;
    border-bottom: 3px solid #34d399;
    color: #a7f3d0;
}

.nightMode .cloze-english,
.night_mode .cloze-english,
body.nightMode .cloze-english,
body.night_mode .cloze-english {
    color: #90cdf4;
    border-top: 1px dashed #4a5568;
}

.nightMode .cloze-answer-box,
.night_mode .cloze-answer-box,
body.nightMode .cloze-answer-box,
body.night_mode .cloze-answer-box {
    background: #2d3748;
    border: 1px solid #4a5568;
}

.nightMode .cloze-answer-label,
.night_mode .cloze-answer-label,
body.nightMode .cloze-answer-label,
body.night_mode .cloze-answer-label {
    color: #a0aec0;
}

.nightMode .cloze-answer-syll,
.night_mode .cloze-answer-syll,
body.nightMode .cloze-answer-syll,
body.night_mode .cloze-answer-syll {
    color: #63b3ed;
}

.nightMode .cloze-answer-phon,
.night_mode .cloze-answer-phon,
body.nightMode .cloze-answer-phon,
body.night_mode .cloze-answer-phon {
    color: #e2e8f0;
}

.nightMode hr#answer,
.night_mode hr#answer,
body.nightMode hr#answer,
body.night_mode hr#answer {
    background: #4a5568;
}

@media (prefers-color-scheme: dark) {
    .card {
        background-color: #20262e;
        color: #e2e8f0;
    }
    .cloze-sentence-syll {
        color: #f7fafc;
    }
    .cloze-sentence-phon {
        color: #cbd5e0;
    }
    .cloze-blank {
        background-color: #78350f;
        border-bottom: 3px solid #f59e0b;
        color: #fef3c7;
    }
    .cloze-target {
        background-color: #064e3b;
        border-bottom: 3px solid #34d399;
        color: #a7f3d0;
    }
    .cloze-english {
        color: #90cdf4;
        border-top: 1px dashed #4a5568;
    }
    .cloze-answer-box {
        background: #2d3748;
        border: 1px solid #4a5568;
    }
    .cloze-answer-label {
        color: #a0aec0;
    }
    .cloze-answer-syll {
        color: #63b3ed;
    }
    .cloze-answer-phon {
        color: #e2e8f0;
    }
    hr#answer {
        background: #4a5568;
    }
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
    conjugations_csv: str = DEFAULT_CONJUGATIONS_CSV,
    audio_dir: str = DEFAULT_AUDIO_DIR,
    official_data_csv: str = DEFAULT_OFFICIAL_DATA_CSV,
    sentence_audio_dir: str = DEFAULT_SENTENCE_AUDIO_DIR,
) -> dict[str, list[AnkiCard]]:
    """
    Generates all 3 types of cards and exports CSVs and HTML templates.
    Classes are ordered by their total verb count (main class + [~~~] subclasses),
    with all subclasses placed immediately after their main class.
    Word audio is mapped onto the Cherokee side of cards, and example sentences with
    audio are included in the ExtraInfo section.
    """
    print("Initializing MascotResolver and loading aspect classes...")
    resolver = MascotResolver()
    aspect_classes = load_aspect_classes()
    class_lookup: dict[str, AspectClass] = {
        c.full_name: c for c in aspect_classes
    }

    # Load word audio and sentence audio mappings
    audio_map, audio_files_by_name = load_audio_mapping(
        csv_path=conjugations_csv, audio_dir=audio_dir
    )
    if audio_map:
        print(f"Loaded {len(audio_map)} word audio mappings ({len(audio_files_by_name)} audio files available)")

    sentence_map, sentence_audio_files_by_name = load_sentence_mapping(
        csv_path=official_data_csv, audio_dir=sentence_audio_dir
    )
    if sentence_map:
        print(f"Loaded {len(sentence_map)} example sentences ({len(sentence_audio_files_by_name)} sentence audio files available)")

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

    deck_main = "Cherokee Roots::Roots & Mascots"
    deck_practice = "Cherokee Roots::Practice"

    # Build Type 1: Mascot Tense Cards
    for c_name in ordered_class_names:
        mascot_verb = class_mascots[c_name]
        cards: list[AnkiCard] = []
        cls_meta = class_lookup.get(c_name) or class_lookup.get(
            c_name.split("[")[0]
        )
        v_eno = str(getattr(mascot_verb.meta, "entry_no", None) or "")
        mascot_sentence = sentence_map.get(v_eno)
        mascot_extra_table = build_verb_table_html(
            c_name,
            mascot_verb,
            is_mascot=True,
            aspect_class=cls_meta,
            sentence_data=mascot_sentence,
        )
        cid_str = str(mascot_verb.corpus_id or mascot_verb.definition)

        for fn, eng_tense, syl_header in FORM_LABELS:
            seg = mascot_verb.segmented_forms.get(fn)
            if not seg or seg == "---":
                continue

            card_id = f"mascot_{c_name}_{fn}_{cid_str}"
            m_def = inflect_english_definition(mascot_verb.definition, fn)
            audio_file = audio_map.get((v_eno, fn))
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
                audio_filename=audio_file,
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
            v_eno = str(getattr(v.meta, "entry_no", None) or "")
            verb_sentence = sentence_map.get(v_eno)
            root_str = v.morphology.h_grade_root
            if (
                v.morphology.glottal_grade_root
                and v.morphology.glottal_grade_root != v.morphology.h_grade_root
            ):
                root_str += f" / {v.morphology.glottal_grade_root}"
            comm_root = unrespell_consonants(root_str)

            # Extra info for this specific member verb
            verb_extra_table = build_verb_table_html(
                c_name,
                v,
                is_mascot=False,
                aspect_class=cls_meta,
                sentence_data=verb_sentence,
                mascot_verb=class_mascots[c_name],
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
                audio_file = audio_map.get((v_eno, fn))
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
                    audio_filename=audio_file,
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
    font_media_files = get_anki_media_files()

    def _get_deck_media(cards: list[AnkiCard]) -> list[str]:
        deck_media = list(font_media_files)
        for c in cards:
            card_text = c.back + " " + c.extra_info
            for sound_name in re.findall(r"\[sound:(.*?)\]", card_text):
                if sound_name in audio_files_by_name:
                    deck_media.append(audio_files_by_name[sound_name])
                elif sound_name in sentence_audio_files_by_name:
                    deck_media.append(sentence_audio_files_by_name[sound_name])
            for sound_name in re.findall(r"Audio\(['\"](.*?)['\"]\)", card_text):
                if sound_name in sentence_audio_files_by_name:
                    deck_media.append(sentence_audio_files_by_name[sound_name])
                elif sound_name in audio_files_by_name:
                    deck_media.append(audio_files_by_name[sound_name])
        return list(dict.fromkeys(deck_media))

    export_targets = [
        ("all_cards_interleaved", "Cherokee Roots::All Interleaved", all_cards),
        ("mascots_and_roots", "Cherokee Roots::Roots & Mascots", mascots_and_roots),
        ("mascots", "Cherokee Roots::Mascots", mascots),
        ("roots", "Cherokee Roots::Roots", roots),
        ("practice", "Cherokee Roots::Practice", practice),
        ("practice_sampled", "Cherokee Roots::Practice (Sampled)", practice_sampled),
    ]

    for basename, deck_name, card_list in export_targets:
        csv_path = os.path.join(ANKI_OUTPUT_DIR, f"{basename}.csv")
        apkg_path = os.path.join(ANKI_OUTPUT_DIR, f"{basename}.apkg")
        write_csv(csv_path, card_list)
        deck_media = _get_deck_media(card_list)
        write_apkg(
            apkg_path,
            deck_name,
            card_list,
            model=cherokee_model,
            media_files=deck_media,
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
"""
    with open(os.path.join(output_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    print(f"Exported Anki documentation and templates to {output_dir}")

