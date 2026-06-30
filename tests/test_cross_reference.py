import csv
import os
import pytest
from noun_pipeline.phases.cross_reference import phase_4_cross_reference

def test_cross_reference_direct(tmp_path):
    # Test direct matching
    noun_stems_file = tmp_path / "test_noun_stems_direct.csv"
    verb_roots_file = tmp_path / "test_verb_roots_direct.csv"
    output_file = tmp_path / "test_output_direct.csv"

    # Write a mock validated noun stem row for 'utlvki'
    with open(noun_stems_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "corpus_id", "original_word", "stem", "structure", "aspect",
            "person", "number", "pronominal_set", "noun_template",
            "verb_root", "paradigm", "is_animate_plural", "is_distributive_plural", "is_valid"
        ])
        writer.writeheader()
        writer.writerow({
            "corpus_id": "651",
            "original_word": "utlvki",
            "stem": "tlvk",
            "structure": "nominal",
            "aspect": "imperfective",
            "person": "3rd",
            "number": "singular",
            "pronominal_set": "b",
            "noun_template": "agentive",
            "verb_root": "tlvk",
            "paradigm": "stative",
            "is_animate_plural": "True",
            "is_distributive_plural": "True",
            "is_valid": "True"
        })

    # Write a mock verb root row for 'utlvka'
    with open(verb_roots_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["root_id", "h_grade", "g_grade", "class", "stem_type", "corpus_ids"])
        writer.writeheader()
        writer.writerow({
            "root_id": "tlvk",
            "h_grade": "tlvk",
            "g_grade": "tlvk",
            "class": "stative",
            "stem_type": "con",
            "corpus_ids": "1559"
        })

    phase_4_cross_reference(
        noun_stems_path=str(noun_stems_file),
        verb_roots_path=str(verb_roots_file),
        output_path=str(output_file)
    )

    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["match_type"] == "direct"


def test_cross_reference_reconstruction(tmp_path):
    # Test reconstruction fallback (by setting verb_root in noun to something different, e.g. empty)
    noun_stems_file = tmp_path / "test_noun_stems_recon.csv"
    verb_roots_file = tmp_path / "test_verb_roots_recon.csv"
    output_file = tmp_path / "test_output_recon.csv"

    # Write a mock validated noun stem row for 'utlvki' with empty verb_root
    with open(noun_stems_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "corpus_id", "original_word", "stem", "structure", "aspect",
            "person", "number", "pronominal_set", "noun_template",
            "verb_root", "paradigm", "is_animate_plural", "is_distributive_plural", "is_valid"
        ])
        writer.writeheader()
        writer.writerow({
            "corpus_id": "651",
            "original_word": "utlvki",
            "stem": "tlvk",
            "structure": "nominal",
            "aspect": "imperfective",
            "person": "3rd",
            "number": "singular",
            "pronominal_set": "b",
            "noun_template": "agentive",
            "verb_root": "", # Bypass direct matching
            "paradigm": "stative",
            "is_animate_plural": "True",
            "is_distributive_plural": "True",
            "is_valid": "True"
        })

    # Write a mock verb root row for 'utlvka'
    with open(verb_roots_file, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["root_id", "h_grade", "g_grade", "class", "stem_type", "corpus_ids"])
        writer.writeheader()
        writer.writerow({
            "root_id": "tlvk",
            "h_grade": "tlvk",
            "g_grade": "tlvk",
            "class": "stative",
            "stem_type": "con",
            "corpus_ids": "1559"
        })

    phase_4_cross_reference(
        noun_stems_path=str(noun_stems_file),
        verb_roots_path=str(verb_roots_file),
        output_path=str(output_file)
    )

    assert output_file.exists()
    with open(output_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 1
    assert rows[0]["match_type"] == "reconstruction"
