from dictionary_pipeline.dictionary_forms import Prediction
from dictionary_pipeline.phases.identify_aspect_classes import get_matches_for_verb
from dictionary_pipeline.phases.preprocess_ced.artifacts import load_corpus
from morphology.morphemes.aspect.pattern_registry import PatternRegistry


def test_wearing_glasses_matching():
    # Initialize the registry and load class patterns
    registry = PatternRegistry.get_instance()
    registry.load_from_csv()

    # Load all corpus rows
    corpus = load_corpus()

    # Find the rows for "wearing glasses" (corpus_id = 729)
    rows_729 = [row for row in corpus if row.meta.corpus_id == "729"]

    assert len(rows_729) > 0, "Could not find any corpus rows with corpus_id = 729"

    predictions = [row.meta.prediction for row in rows_729]
    print(f"\nPredictions attempted for row 729: {predictions}")

    assert (
        Prediction.FULL_STATIVE in predictions
    ), "Expected FullStative prediction to be attempted"
    assert (
        Prediction.INF_EVENTFUL in predictions
    ), "Expected InfEventful prediction to be attempted"

    inf_eventful_row = next(
        row for row in rows_729 if row.meta.prediction == Prediction.INF_EVENTFUL
    )
    full_stative_row = next(
        row for row in rows_729 if row.meta.prediction == Prediction.FULL_STATIVE
    )

    # Call matching logic
    inf_matches = get_matches_for_verb(inf_eventful_row, registry)
    full_stative_matches = get_matches_for_verb(full_stative_row, registry)

    print(f"InfEventful matches: {inf_matches}")
    print(f"FullStative matches: {full_stative_matches}")

    # For InfEventful predictions, it should match the aspect class hvsk-han
    inf_match_classes = [m["class"] for m in inf_matches]
    assert (
        "hvsk-han" in inf_match_classes
    ), f"Expected InfEventful to match 'hvsk-han', but got {inf_match_classes}"
