"""
Unit tests for Anki flashcard generation package.
"""

import os
import pytest

from anki.formatter import (
    FORM_LABELS,
    build_card_back_html,
    build_card_front_html,
    build_class_table_html,
    format_segmented_verb_html,
    format_template_html,
)
from anki.generator import generate_anki_cards
from anki.models import AnkiCard
from anki.sequencer import AnkiSequencer
from dictionary_pipeline.paths import ARTIFACTS_DIR


def test_anki_card_model():
    card = AnkiCard(
        card_id="test_1",
        card_type="mascot_tense",
        deck="Cherokee Roots::Roots & Mascots",
        sequence_order=1,
        class_name="ih-ohd",
        verb_id="361",
        definition="he/she is attempting it",
        root="anelht",
        tense="Present",
        front="<div>Front</div>",
        back="<div>Back</div>",
        extra_info="<div>Extra</div>",
        tags=["cherokee", "class::ih-ohd"],
    )

    row = card.to_csv_row()
    assert row["Id"] == "test_1"
    assert row["CardType"] == "mascot_tense"
    assert row["Deck"] == "Cherokee Roots::Roots & Mascots"
    assert row["SequenceOrder"] == "1"
    assert row["Class"] == "ih-ohd"
    assert row["Tags"] == "cherokee class::ih-ohd"

    fields = AnkiCard.get_csv_fieldnames()
    assert set(fields) == set(row.keys())


def test_anki_generator_and_exports():
    results = generate_anki_cards(initial_batch_size=5, interleave_batch_size=3)

    assert len(results["mascots"]) > 0
    assert len(results["roots"]) > 0
    assert len(results["practice"]) > 0
    assert len(results["practice_sampled"]) > 0
    assert len(results["practice_sampled"]) < len(results["practice"])
    assert len(results["mascots_and_roots"]) == len(results["mascots"]) + len(results["roots"])
    assert len(results["all_cards"]) == len(results["mascots_and_roots"]) + len(results["practice"])

    # Check files exist on disk
    anki_dir = os.path.join(ARTIFACTS_DIR, "anki")
    assert os.path.exists(os.path.join(anki_dir, "all_cards_interleaved.csv"))
    assert os.path.exists(os.path.join(anki_dir, "all_cards_interleaved.apkg"))
    assert os.path.exists(os.path.join(anki_dir, "mascots_and_roots.csv"))
    assert os.path.exists(os.path.join(anki_dir, "mascots_and_roots.apkg"))
    assert os.path.exists(os.path.join(anki_dir, "mascots.csv"))
    assert os.path.exists(os.path.join(anki_dir, "mascots.apkg"))
    assert os.path.exists(os.path.join(anki_dir, "roots.csv"))
    assert os.path.exists(os.path.join(anki_dir, "roots.apkg"))
    assert os.path.exists(os.path.join(anki_dir, "practice.csv"))
    assert os.path.exists(os.path.join(anki_dir, "practice.apkg"))
    assert os.path.exists(os.path.join(anki_dir, "practice_sampled.csv"))
    assert os.path.exists(os.path.join(anki_dir, "practice_sampled.apkg"))
    assert os.path.exists(os.path.join(anki_dir, "styling.css"))
    assert os.path.exists(os.path.join(anki_dir, "front_template.html"))
    assert os.path.exists(os.path.join(anki_dir, "back_template.html"))
    assert os.path.exists(os.path.join(anki_dir, "card1_front.html"))
    assert os.path.exists(os.path.join(anki_dir, "card1_back.html"))
    assert os.path.exists(os.path.join(anki_dir, "card2_front.html"))
    assert os.path.exists(os.path.join(anki_dir, "card2_back.html"))
    assert os.path.exists(os.path.join(anki_dir, "README.md"))


def test_anki_apkg_structure():
    import json
    import sqlite3
    import tempfile
    import zipfile
    from anki.generator import get_cherokee_model

    anki_dir = os.path.join(ARTIFACTS_DIR, "anki")
    apkg_path = os.path.join(anki_dir, "mascots_and_roots.apkg")
    assert os.path.exists(apkg_path)

    tmpdir = tempfile.mkdtemp()
    with zipfile.ZipFile(apkg_path, "r") as z:
        z.extractall(tmpdir)
        assert "collection.anki2" in z.namelist()
        assert "media" in z.namelist()

    conn = sqlite3.connect(os.path.join(tmpdir, "collection.anki2"))
    cur = conn.cursor()

    models_json, = cur.execute("SELECT models FROM col").fetchone()
    models = json.loads(models_json)
    model = list(models.values())[0]

    # Reversible model check: 2 templates
    assert len(model["tmpls"]) == 2
    assert model["tmpls"][0]["name"] == "Card 1: English -> Cherokee"
    assert model["tmpls"][1]["name"] == "Card 2: Cherokee -> English"

    # Card count should be 2x note count
    card_count, = cur.execute("SELECT count(*) FROM cards").fetchone()
    note_count, = cur.execute("SELECT count(*) FROM notes").fetchone()
    assert note_count == 1022
    assert card_count == note_count * 2

    # Cards have explicit sequence order due
    cards_rows = cur.execute(
        "SELECT ord, queue, due FROM cards ORDER BY due, ord LIMIT 4"
    ).fetchall()
    assert cards_rows[0] == (0, 0, 1)
    assert cards_rows[1] == (1, 0, 1)
    assert cards_rows[2] == (0, 0, 2)
    assert cards_rows[3] == (1, 0, 2)


def test_practice_sampling_and_filtered_tags():
    filter_tag = "filtered"
    results = generate_anki_cards(
        sample_practice_min=1,
        sample_practice_max=2,
        filter_tag=filter_tag,
    )

    practice_cards = results["practice"]
    practice_sampled = results["practice_sampled"]

    # Group practice cards by verb_id
    by_verb = {}
    for c in practice_cards:
        by_verb.setdefault(c.verb_id, []).append(c)

    for vid, cards in by_verb.items():
        unfiltered = [c for c in cards if filter_tag not in c.tags]
        filtered = [c for c in cards if filter_tag in c.tags]

        # Exactly 1 or 2 cards per verb must be unfiltered
        expected_unfiltered = min(len(cards), 2)
        assert 1 <= len(unfiltered) <= 2
        assert len(unfiltered) + len(filtered) == len(cards)

    # Verify practice_sampled contains only unfiltered cards
    assert all(filter_tag not in c.tags for c in practice_sampled)
    assert len(practice_sampled) == sum(1 for c in practice_cards if filter_tag not in c.tags)


def test_sequencer_invariants():
    results = generate_anki_cards()
    all_cards = results["all_cards"]

    # Verify every card has a unique, positive, monotonically increasing SequenceOrder in all_cards
    seq_orders = [c.sequence_order for c in all_cards]
    assert seq_orders == list(range(1, len(all_cards) + 1))

    # Verify that for every verb with a root card and practice cards,
    # the root card strictly appears BEFORE any practice card for that verb
    root_positions = {}
    practice_positions = {}

    for c in all_cards:
        if c.card_type == "verb_root":
            root_positions[c.verb_id] = c.sequence_order
        elif c.card_type == "practice_test":
            practice_positions.setdefault(c.verb_id, []).append(c.sequence_order)

    for vid, p_seqs in practice_positions.items():
        if vid in root_positions:
            r_seq = root_positions[vid]
            for p_seq in p_seqs:
                assert r_seq < p_seq, f"Root card {vid} (order {r_seq}) must precede practice card (order {p_seq})"


def test_english_semantic_inflections():
    from anki.english_inflector import inflect_english_definition

    # 1. Standard action verb
    d1 = "he/she is attempting it"
    assert inflect_english_definition(d1, "present") == "she is attempting it"
    assert inflect_english_definition(d1, "imperfective") == "she attempts it"
    assert inflect_english_definition(d1, "perfective") == "she attempted it"
    assert inflect_english_definition(d1, "present_1sg") == "I am attempting it"
    assert inflect_english_definition(d1, "imperative") == "attempt it!"
    assert inflect_english_definition(d1, "infinitive") == "(for her) to attempt it"

    # 2. Reflexive verb (person adaptation)
    d2 = "he/she is fanning himself/herself"
    assert inflect_english_definition(d2, "present") == "she is fanning herself"
    assert inflect_english_definition(d2, "imperfective") == "she fans herself"
    assert inflect_english_definition(d2, "perfective") == "she fanned herself"
    assert inflect_english_definition(d2, "present_1sg") == "I am fanning myself"
    assert inflect_english_definition(d2, "imperative") == "fan yourself!"
    assert inflect_english_definition(d2, "infinitive") == "(for her) to fan herself"

    # 3. Stative verb
    d3 = "he/she wants it"
    assert inflect_english_definition(d3, "present") == "she wants it"
    assert inflect_english_definition(d3, "imperfective") == "she wants it (habitually)"
    assert inflect_english_definition(d3, "perfective") == "she wanted it"
    assert inflect_english_definition(d3, "present_1sg") == "I want it"
    assert inflect_english_definition(d3, "imperative") == "want it!"
    assert inflect_english_definition(d3, "infinitive") == "(for her) to want it"

    # 4. Weather / Impersonal verb
    d4 = "it\u2019s snowing"
    assert inflect_english_definition(d4, "present") == "it is snowing"
    assert inflect_english_definition(d4, "imperfective") == "it snows"
    assert inflect_english_definition(d4, "perfective") == "it snowed"
    assert inflect_english_definition(d4, "imperative") == "snow!"
    assert inflect_english_definition(d4, "infinitive") == "(for it) to snow"

    # 5. Plural verb
    d5 = "they are gathering"
    assert inflect_english_definition(d5, "present") == "they are gathering"
    assert inflect_english_definition(d5, "imperfective") == "they gather"
    assert inflect_english_definition(d5, "perfective") == "they gathered"
    assert inflect_english_definition(d5, "imperative") == "gather!"
    assert inflect_english_definition(d5, "infinitive") == "(for them) to gather"


def test_audio_mapping_and_card_integration():
    from anki.generator import load_audio_mapping

    audio_map, audio_files_by_name = load_audio_mapping()
    assert len(audio_map) > 0
    assert len(audio_files_by_name) > 0

    # Verify specific known audio mapping: Entry 10 (bouncing it), Present -> Word_0010.1.m4a
    assert ("10", "present") in audio_map
    assert audio_map[("10", "present")] == "Word_0010.1.m4a"

    # Verify generate_anki_cards attaches audio
    results = generate_anki_cards()
    all_cards = results["all_cards"]
    cards_with_audio = [c for c in all_cards if "[sound:" in c.back]
    assert len(cards_with_audio) == 170

    # Verify mascot cards have audio when available
    mascot_audio = [c for c in results["mascots"] if "[sound:" in c.back]
    assert len(mascot_audio) > 0

    # Verify practice cards have audio when available
    practice_audio = [c for c in results["practice"] if "[sound:" in c.back]
    assert len(practice_audio) > 0

    # Verify root cards do not have sound tags
    root_audio = [c for c in results["roots"] if "[sound:" in c.back]
    assert len(root_audio) == 0

    # Verify APKG package includes audio media files
    import json
    import tempfile
    import zipfile
    anki_dir = os.path.join(ARTIFACTS_DIR, "anki")
    apkg_path = os.path.join(anki_dir, "all_cards_interleaved.apkg")
    assert os.path.exists(apkg_path)

    tmpdir = tempfile.mkdtemp()
    with zipfile.ZipFile(apkg_path, "r") as z:
        z.extractall(tmpdir)
        assert "media" in z.namelist()
        with open(os.path.join(tmpdir, "media"), "r", encoding="utf-8") as f:
            media_map = json.load(f)
            media_values = set(media_map.values())
            # Check font is present
            assert "_NotoSansCherokee-Regular.ttf" in media_values
    # Verify sentence examples and sentence audio
    from anki.generator import load_sentence_mapping

    sent_map, sent_audio_files = load_sentence_mapping()
    assert len(sent_map) > 0
    assert len(sent_audio_files) > 0

    # Verify Entry 8 has sentence and sentence audio
    assert "8" in sent_map
    assert sent_map["8"]["audio"] == "Sentence_for_entry_0008.m4a"

    # Verify cards have example sentence and sentence audio in extra_info
    cards_with_sentence_audio = [c for c in all_cards if "Sentence_for_entry_" in c.extra_info]
    assert len(cards_with_sentence_audio) > 3000

    # Verify sentence order: phonetics first, then syllabary, then english
    sample_card = [c for c in all_cards if "Sentence_for_entry_0008.m4a" in c.extra_info][0]
    extra = sample_card.extra_info
    assert "Example Sentence" in extra
    phon_pos = extra.find("e:ladí")
    syll_pos = extra.find("ᎡᎳᏗ")
    engl_pos = extra.find("When he threw")
    assert phon_pos != -1 and syll_pos != -1 and engl_pos != -1
    assert phon_pos < syll_pos < engl_pos

    # Check sentence audio file is in the APKG package media
    assert "Sentence_for_entry_0008.m4a" in media_values


def test_cloze_card_model():
    from anki.models import ClozeCard
    from anki.cloze_generator import get_cloze_model

    card = ClozeCard(
        card_id="cloze_4.1_s1_w2",
        deck="Cherokee Cloze Sentences",
        sequence_order=2,
        entry_no="4.1",
        word_index=2,
        total_words=4,
        english="The boys are playing ball.",
        front_syllabary="Ꮎ <span class='cloze-blank'>______</span> ᏍᏆᏞᏍᏗ ᏓᎾᏁᎶᎲᏍᎦ.",
        front_phonetics="ná <span class='cloze-blank'>______</span> sgwà:hle̋:sdi dà:ná:ne:lo:hv́sga",
        target_word_syllabary="ᎠᏂᏧᏣ",
        target_word_phonetics="ani:chű:ja",
        back_syllabary="Ꮎ <span class='cloze-target'>ᎠᏂᏧᏣ</span> ᏍᏆᏞᏍᏗ ᏓᎾᏁᎶᎲᏍᎦ.",
        back_phonetics="ná <span class='cloze-target'>ani:chű:ja</span> sgwà:hle̋:sdi dà:ná:ne:lo:hv́sga",
        audio="[sound:Sentence_for_entry_0004.m4a]",
        tags=["cloze", "sentence", "entry_4"],
    )

    row = card.to_csv_row()
    assert row["Id"] == "cloze_4.1_s1_w2"
    assert row["TargetWordSyllabary"] == "ᎠᏂᏧᏣ"
    assert row["WordIndex"] == "2"
    assert row["TotalWords"] == "4"
    assert row["Tags"] == "cloze sentence entry_4"

    fields = ClozeCard.get_csv_fieldnames()
    assert set(fields) == set(row.keys())

    model = get_cloze_model()
    note = card.to_genanki_note(model)
    assert note.guid is not None
    assert len(note.fields) == 14


def test_cloze_card_generation_and_exports():
    import json
    import tempfile
    import zipfile
    from anki.cloze_generator import generate_cloze_cards
    from anki.generator import DEFAULT_OFFICIAL_DATA_CSV, DEFAULT_SENTENCE_AUDIO_DIR

    anki_dir = os.path.join(ARTIFACTS_DIR, "anki")
    cloze_cards = generate_cloze_cards(
        official_data_csv=DEFAULT_OFFICIAL_DATA_CSV,
        sentence_audio_dir=DEFAULT_SENTENCE_AUDIO_DIR,
        output_dir=anki_dir,
    )

    assert len(cloze_cards) > 7000

    csv_path = os.path.join(anki_dir, "cloze_sentences.csv")
    apkg_path = os.path.join(anki_dir, "cloze_sentences.apkg")
    front_template = os.path.join(anki_dir, "cloze_front.html")
    back_template = os.path.join(anki_dir, "cloze_back.html")

    assert os.path.exists(csv_path)
    assert os.path.exists(apkg_path)
    assert os.path.exists(front_template)
    assert os.path.exists(back_template)

    # Verify APKG package contents
    tmpdir = tempfile.mkdtemp()
    with zipfile.ZipFile(apkg_path, "r") as z:
        z.extractall(tmpdir)
        assert "collection.anki2" in z.namelist()
        assert "media" in z.namelist()
        with open(os.path.join(tmpdir, "media"), "r", encoding="utf-8") as f:
            media_map = json.load(f)
            media_values = set(media_map.values())
            assert "Sentence_for_entry_0004.m4a" in media_values
            assert len(media_values) > 1800


def test_mascot_header_on_member_verb_cards():
    """Verify that root and practice cards contain class mascot info in ExtraInfo."""
    from anki.formatter import build_verb_table_html
    from tex_dictionary.mascot_resolver import MascotResolver

    resolver = MascotResolver()
    # Find a class with mascot and member verbs
    c_name = "ih-ohd"
    mascot_verb = resolver.resolve_mascot(c_name, "Plain")
    assert mascot_verb is not None

    member_verbs = [
        v for v in resolver.all_verbs
        if v.morphology.class_name == c_name
        and v.corpus_id != mascot_verb.corpus_id
    ]
    assert len(member_verbs) > 0
    sample_member = member_verbs[0]

    from dictionary_pipeline.orthography import unrespell_consonants

    # 1. Non-mascot verb table with mascot_verb passed
    member_html = build_verb_table_html(
        class_name=c_name,
        verb=sample_member,
        is_mascot=False,
        mascot_verb=mascot_verb,
    )
    assert "Class Mascot:" in member_html
    m_comm_root = unrespell_consonants(mascot_verb.morphology.h_grade_root)
    assert f"-{m_comm_root}-" in member_html
    assert "Verb:" in member_html

    # 2. Mascot verb table with is_mascot=True
    mascot_html = build_verb_table_html(
        class_name=c_name,
        verb=mascot_verb,
        is_mascot=True,
    )
    assert "Class Mascot:" not in mascot_html
    assert "Mascot:" in mascot_html

    # 3. Test generated cards via generate_anki_cards
    results = generate_anki_cards(initial_batch_size=2, interleave_batch_size=2)
    root_cards = results["roots"]
    practice_cards = results["practice"]
    mascot_cards = results["mascots"]

    # All root cards for member verbs must have Class Mascot in extra_info
    for card in root_cards:
        assert "Class Mascot:" in card.extra_info
        assert "Class:" in card.extra_info
        assert "Verb:" in card.extra_info

    # All practice cards must have Class Mascot in extra_info
    for card in practice_cards:
        assert "Class Mascot:" in card.extra_info
        assert "Class:" in card.extra_info
        assert "Verb:" in card.extra_info

    # Mascot cards must NOT have a redundant Class Mascot subline
    for card in mascot_cards:
        assert "Class Mascot:" not in card.extra_info
        assert "Mascot:" in card.extra_info


def test_root_cards_have_full_template():
    """Verify that root cards display the whole verb template rather than just -root-."""
    from anki.formatter import format_template_html, format_template_plain
    from tex_dictionary.mascot_resolver import MascotResolver

    resolver = MascotResolver()
    sample_verb = next(v for v in resolver.all_verbs if v.morphology.class_name == "eg-invs" and str(v.corpus_id) == "4")
    
    html_template = format_template_html(sample_verb)
    plain_template = format_template_plain(sample_verb)

    # Must contain pronoun set, middle voice if any, bold root, and class
    assert "Set A" in html_template
    assert "ad" in html_template
    assert "[eg-invs]" in html_template
    assert "strong" in html_template
    assert "Set A-at-ad-[eg-invs]" == plain_template

    # Check back of root card
    back_html = build_card_back_html("verb_root", sample_verb)
    assert "cherokee-template" in back_html
    assert "Set A" in back_html
    assert "[eg-invs]" in back_html
    # Should not be just "-ad-"
    assert "-ad-" not in back_html


def test_kirk_importance_ordering_within_class():
    """Verify that within a class, higher importance Kirk verbs come before lower ones after mascot."""
    from anki.verb_priority import compute_verb_priority, load_kirk_verbs
    from tex_dictionary.mascot_resolver import MascotResolver

    kirk_verbs = load_kirk_verbs()
    assert len(kirk_verbs) == 455

    resolver = MascotResolver()
    priority_map = compute_verb_priority(resolver.all_verbs)

    # Class ih-ohd member verbs: check that watching (cid=1593, Tier 2) precedes bouncing it (cid=6, Tier 6)
    v_watching = next((v for v in resolver.all_verbs if v.corpus_id == "1593"), None)
    v_bouncing = next((v for v in resolver.all_verbs if v.corpus_id == "6"), None)

    if v_watching and v_bouncing:
        assert priority_map[id(v_watching)][0] < priority_map[id(v_bouncing)][0]

    # Verify generate_anki_cards respects this ordering
    results = generate_anki_cards(initial_batch_size=5, interleave_batch_size=3)
    roots = results["roots"]

    # Filter roots for class ih-ohd
    ih_ohd_roots = [c for c in roots if c.class_name == "ih-ohd"]
    assert len(ih_ohd_roots) >= 2

    # Verify that in ih-ohd roots, watching appears before bouncing it
    watching_idx = next(i for i, c in enumerate(ih_ohd_roots) if c.verb_id == "1593")
    bouncing_idx = next(i for i, c in enumerate(ih_ohd_roots) if c.verb_id == "6")
    assert watching_idx < bouncing_idx




