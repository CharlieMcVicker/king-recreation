from dictionary_pipeline.dictionary_forms import Prediction, build_wordspec
from morphology.morphemes.prefixes.pronominals import PronominalConfig, StemType
from morphology.word_spec import Aspect, Number, Person, PronominalSet


def test_build_wordspec_present_1sg():
    config = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
    )
    spec = build_wordspec(Prediction.FULL_EVENTFUL, config, "present_1sg")
    assert spec.aspect == Aspect.PRESENT
    assert spec.person == Person.FIRST
    assert spec.number == Number.SINGULAR
    assert spec.pronominal_set == PronominalSet.SET_A


def test_build_wordspec_infinitive_plural():
    config = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT, plural_pronouns=True
    )
    spec = build_wordspec(Prediction.FULL_EVENTFUL, config, "infinitive")
    assert spec.aspect == Aspect.INFINITIVE
    # infinitive always uses Set B pronouns regardless of stative/set_a
    assert spec.person == Person.THIRD
    assert spec.number == Number.PLURAL
    assert spec.pronominal_set == PronominalSet.SET_B


def test_build_wordspec_imperative_to_3rd():
    config = PronominalConfig(
        set_type=PronominalSet.SET_A,
        stem_type=StemType.CONSONANT,
        use_3rd_person_object=True,
    )
    spec = build_wordspec(Prediction.FULL_STATIVE, config, "imperative")
    assert spec.aspect == Aspect.IMPERATIVE
    assert spec.person == Person.SECOND_TO_THIRD
    assert spec.number == Number.SINGULAR
    assert spec.pronominal_set == PronominalSet.PERSON_TO_PERSON


def test_build_wordspec_perfective_stative():
    config = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
    )
    # Perfective for Set A + Stative should use Set A
    spec = build_wordspec(Prediction.FULL_STATIVE, config, "perfective")
    assert spec.person == Person.THIRD
    assert spec.number == Number.SINGULAR
    assert spec.pronominal_set == PronominalSet.SET_A

    # Perfective for Set A + NON-Stative should use Set B
    spec = build_wordspec(Prediction.FULL_EVENTFUL, config, "perfective")
    assert spec.person == Person.THIRD
    assert spec.number == Number.SINGULAR
    assert spec.pronominal_set == PronominalSet.SET_B


def test_build_wordspec_imperfective():
    config = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
    )
    spec = build_wordspec(Prediction.FULL_EVENTFUL, config, "imperfective")
    assert spec.aspect == Aspect.IMPERFECTIVE
    assert spec.person == Person.THIRD
    assert spec.number == Number.SINGULAR
    assert spec.pronominal_set == PronominalSet.SET_A
