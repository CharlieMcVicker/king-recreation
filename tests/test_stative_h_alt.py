from king_recreation.morphemes.aspect.pattern_registry import PatternRegistry
from king_recreation.phases.identify_aspect_classes import get_matches_for_verb
from king_recreation.phases.preprocess_ced.artifacts import load_corpus


def test_be_alive():
    corpus = load_corpus()
    verb_be_alive = next(row for row in corpus if row["corpus_id"] == "1067")
    assert verb_be_alive
    registry = PatternRegistry.get_instance()
    registry.load_from_csv()

    candidates = registry.get_candidates(
        verb_be_alive["present_1sg"], "present", allow_suffix_alternation=True
    )
    classes = set(c.name for c in candidates)
    assert "stative-h" in classes

    matches = get_matches_for_verb(verb_be_alive, registry)
    classes = set(m["class"] for m in matches)
    assert "stative-h" in classes
