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
        deck="Cherokee::Roots & Mascots",
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
    assert row["Deck"] == "Cherokee::Roots & Mascots"
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
