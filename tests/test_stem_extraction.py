from morphology.word_spec import NounStructure, get_noun_wordspec
from noun_pipeline.phases.extract_stems import extract_and_validate_stems
from noun_pipeline.phases.generate_hypotheses import NounHypothesis


def test_extract_and_validate_valid_stem():
    word_spec = get_noun_wordspec(NounStructure.INCOMPLETIVE)

    # Example: "yanv'i" is an incompletive verb form. Let's see if the aspect suffix matching extracts the root correctly.
    # The suffix "-v'i" should match incompletive pattern in some classes.
    h = NounHypothesis(
        original_word="somesuiv'i",
        word_spec=word_spec,
        stem="somesui",  # Phase 2 strips v'i
        noun_template=NounStructure.INCOMPLETIVE.value,
    )

    validated = extract_and_validate_stems([h])

    assert len(validated) == 1
    val = validated[0]

    assert val.is_valid
    assert val.verb_root == "somesui"
    assert val.paradigm != ""


def test_extract_and_validate_reject_bad_plural():
    word_spec = get_noun_wordspec(NounStructure.INCOMPLETIVE)

    # Example: we give a plural that shouldn't match any generated forms
    h = NounHypothesis(
        original_word="somesuiv'i",
        word_spec=word_spec,
        stem="somesui",
        noun_template=NounStructure.INCOMPLETIVE.value,
        plural_word="wrongplural",
    )

    validated = extract_and_validate_stems([h])

    assert len(validated) == 1
    assert not validated[0].is_valid


def test_extract_and_validate_inanimate_plural():
    from morphology.morphology_types import Number, Person, PronominalSet

    word_spec = get_noun_wordspec(
        NounStructure.AGENTIVE, Person.THIRD, Number.SINGULAR, PronominalSet.SET_A
    )

    h = NounHypothesis(
        original_word="atana'nv'i",
        word_spec=word_spec,
        stem="tana'nv'",
        noun_template=NounStructure.AGENTIVE.value,
        plural_word="tatana'nv'i",
    )

    validated = extract_and_validate_stems([h])

    assert len(validated) >= 1

    valid_results = [v for v in validated if v.is_valid]
    assert len(valid_results) >= 1
    val = valid_results[0]

    assert not val.is_animate_plural
    assert val.is_distributive_plural
