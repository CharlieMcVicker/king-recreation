import csv
import os

from noun_pipeline.phases.create_corpus import NOUNS_CORPUS_PATH, create_corpus


def test_noun_corpus_creation():
    # Make sure corpus is created
    if os.path.exists(NOUNS_CORPUS_PATH):
        os.remove(NOUNS_CORPUS_PATH)

    create_corpus()

    assert os.path.exists(NOUNS_CORPUS_PATH)

    with open(NOUNS_CORPUS_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) > 0
    # Check headers
    first_row = rows[0]
    assert "corpus_id" in first_row
    assert "entry_no" in first_row
    assert "definition" in first_row
    assert "singular" in first_row
    assert "plural" in first_row
    assert "animate" in first_row
