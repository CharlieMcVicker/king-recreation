from dictionary_pipeline.dictionary_forms import Prediction
from dictionary_pipeline.phases.identify_aspect_classes import get_matches_for_verb
from dictionary_pipeline.phases.preprocess_ced.artifacts import load_corpus
from morphology.morphemes.aspect.pattern_registry import PatternRegistry


def test_feels_infeventful():
    # Initialize the registry and load class patterns
    registry = PatternRegistry.get_instance()
    registry.load_from_csv()

    # Load all corpus rows
    corpus = load_corpus()

    # Find the row for feels (corpus_id = 1462) with prediction = InfEventful
    feels_row = None
    for row in corpus:
        if (
            row.meta.corpus_id == "1462"
            and row.meta.prediction == Prediction.INF_EVENTFUL
        ):
            feels_row = row
            break

    assert (
        feels_row is not None
    ), "Could not find feels (1462) with InfEventful prediction"

    print("\n--- Examining Verb 1462 (feels) for InfEventful prediction ---")
    print(f"Definition: {feels_row.meta.definition}")
    print(f"Prediction: {feels_row.meta.prediction}")
    print(f"Forms: {feels_row.forms}")

    # Call the matching logic
    matches = get_matches_for_verb(feels_row, registry)
    print(f"Matches found: {matches}")
