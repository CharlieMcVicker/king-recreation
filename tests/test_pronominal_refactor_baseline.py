from dictionary_pipeline.dictionary_forms import FormSpec, calculate_pronominal_key
from morphology.morphemes.prefixes.pronominals import (
    PronominalConfig,
    StemType,
    get_prefix_details,
)
from morphology.word_spec import Aspect, Number, Person, PronominalSet


def test_calculate_set_name_baseline():
    # Test all combinations of aspect and person for a simple Set A consonant stem
    config = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
    )

    fs_present_1st = FormSpec(
        name="present_1sg",
        aspect=Aspect.PRESENT,
        person=Person.FIRST,
        allow_set_a=True,
        stative=False,
    )
    fs_present_2nd = FormSpec(
        name="imperative",
        aspect=Aspect.PRESENT,
        person=Person.SECOND,
        allow_set_a=True,
        stative=False,
    )
    fs_present_3rd = FormSpec(
        name="present",
        aspect=Aspect.PRESENT,
        person=Person.THIRD,
        allow_set_a=True,
        stative=False,
    )
    fs_perfective_1st = FormSpec(
        name="perfective",
        aspect=Aspect.PERFECTIVE,
        person=Person.FIRST,
        allow_set_a=False,
        stative=False,
    )
    fs_perfective_3rd = FormSpec(
        name="perfective",
        aspect=Aspect.PERFECTIVE,
        person=Person.THIRD,
        allow_set_a=False,
        stative=False,
    )
    fs_infinitive_1st = FormSpec(
        name="infinitive",
        aspect=Aspect.INFINITIVE,
        person=Person.FIRST,
        allow_set_a=False,
        stative=False,
    )

    # Eventful non-perfective/infinitive aspects
    assert calculate_pronominal_key(fs_present_1st, config) == (
        Person.FIRST,
        Number.SINGULAR,
        PronominalSet.SET_A,
    )
    assert calculate_pronominal_key(fs_present_2nd, config) == (
        Person.SECOND,
        Number.SINGULAR,
        PronominalSet.SET_A,
    )
    assert calculate_pronominal_key(fs_present_3rd, config) == (
        Person.THIRD,
        Number.SINGULAR,
        PronominalSet.SET_A,
    )

    # Perfective/Infinitive force Set B
    assert calculate_pronominal_key(fs_perfective_1st, config) == (
        Person.FIRST,
        Number.SINGULAR,
        PronominalSet.SET_B,
    )
    assert calculate_pronominal_key(fs_infinitive_1st, config) == (
        Person.FIRST,
        Number.SINGULAR,
        PronominalSet.SET_B,
    )

    # Plurality
    config_pl = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT, plural_pronouns=True
    )
    assert calculate_pronominal_key(fs_present_1st, config_pl) == (
        Person.FIRST,
        Number.PLURAL,
        PronominalSet.SET_A,
    )
    assert calculate_pronominal_key(fs_perfective_3rd, config_pl) == (
        Person.THIRD,
        Number.PLURAL,
        PronominalSet.SET_B,
    )

    # Person to Person
    config_p2p = PronominalConfig(
        set_type=PronominalSet.SET_A,
        stem_type=StemType.CONSONANT,
        use_3rd_person_object=True,
    )
    assert calculate_pronominal_key(fs_present_1st, config_p2p) == (
        Person.FIRST_TO_THIRD,
        Number.SINGULAR,
        PronominalSet.PERSON_TO_PERSON,
    )
    assert calculate_pronominal_key(fs_present_2nd, config_p2p) == (
        Person.SECOND_TO_THIRD,
        Number.SINGULAR,
        PronominalSet.PERSON_TO_PERSON,
    )


def test_get_prefix_details_baseline():
    config = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
    )

    # Check some core prefixes
    assert (
        get_prefix_details(
            (Person.FIRST, Number.SINGULAR, PronominalSet.SET_A), config
        ).form
        == "tsi"
    )
    assert (
        get_prefix_details(
            (Person.FIRST, Number.SINGULAR, PronominalSet.SET_B), config
        ).form
        == "ak"
    )
    assert (
        get_prefix_details(
            (Person.THIRD, Number.SINGULAR, PronominalSet.SET_B), config
        ).form
        == "u"
    )

    config_v = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.VOWEL_A
    )
    assert (
        get_prefix_details(
            (Person.FIRST, Number.SINGULAR, PronominalSet.SET_A), config_v
        ).form
        == "k"
    )
    assert (
        get_prefix_details(
            (Person.FIRST, Number.SINGULAR, PronominalSet.SET_B), config_v
        ).form
        == "akw"
    )
