from king_recreation.morphemes.prefixes.pronominals import (
    PronominalConfig,
    StemType,
    get_prefix_details,
)
from king_recreation.word_spec import (
    Aspect,
    Number,
    Person,
    PronominalSet,
    calculate_pronominal_key,
)


def test_calculate_set_name_baseline():
    # Test all combinations of aspect and person for a simple Set A consonant stem
    config = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
    )

    # Eventful non-perfective/infinitive aspects
    assert calculate_pronominal_key(Aspect.PRESENT, Person.FIRST, config, False) == (
        Person.FIRST,
        Number.SINGULAR,
        PronominalSet.SET_A,
    )
    assert calculate_pronominal_key(Aspect.PRESENT, Person.SECOND, config, False) == (
        Person.SECOND,
        Number.SINGULAR,
        PronominalSet.SET_A,
    )
    assert calculate_pronominal_key(Aspect.PRESENT, Person.THIRD, config, False) == (
        Person.THIRD,
        Number.SINGULAR,
        PronominalSet.SET_A,
    )

    # Perfective/Infinitive force Set B
    assert calculate_pronominal_key(Aspect.PERFECTIVE, Person.FIRST, config, False) == (
        Person.FIRST,
        Number.SINGULAR,
        PronominalSet.SET_B,
    )
    assert calculate_pronominal_key(Aspect.INFINITIVE, Person.FIRST, config, False) == (
        Person.FIRST,
        Number.SINGULAR,
        PronominalSet.SET_B,
    )

    # Plurality
    config_pl = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT, plural_pronouns=True
    )
    assert calculate_pronominal_key(Aspect.PRESENT, Person.FIRST, config_pl, False) == (
        Person.FIRST,
        Number.PLURAL,
        PronominalSet.SET_A,
    )
    assert calculate_pronominal_key(
        Aspect.PERFECTIVE, Person.THIRD, config_pl, False
    ) == (Person.THIRD, Number.PLURAL, PronominalSet.SET_B)

    # Person to Person
    config_p2p = PronominalConfig(
        set_type=PronominalSet.SET_A,
        stem_type=StemType.CONSONANT,
        use_3rd_person_object=True,
    )
    assert calculate_pronominal_key(
        Aspect.PRESENT, Person.FIRST, config_p2p, False
    ) == (Person.FIRST_TO_THIRD, Number.SINGULAR, PronominalSet.PERSON_TO_PERSON)
    assert calculate_pronominal_key(
        Aspect.PRESENT, Person.SECOND, config_p2p, False
    ) == (Person.SECOND_TO_THIRD, Number.SINGULAR, PronominalSet.PERSON_TO_PERSON)


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
