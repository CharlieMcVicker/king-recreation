from king_recreation.morphemes.prefixes.pronominals import PronominalConfig, StemType
from king_recreation.word_spec import build_wordspec


def test_build_wordspec_present_1sg():
    config = PronominalConfig(set_type="a", stem_type=StemType.CONSONANT)
    spec = build_wordspec("present_1sg", config, stative=False)
    assert spec.aspect == "present"
    assert spec.set_name == "1st Set A"


def test_build_wordspec_infinitive_plural():
    config = PronominalConfig(
        set_type="a", stem_type=StemType.CONSONANT, plural_pronouns=True
    )
    spec = build_wordspec("infinitive", config, stative=False)
    assert spec.aspect == "infinitive"
    # infinitive always uses Set B pronouns regardless of stative/set_a
    assert spec.set_name == "3pl Set B"


def test_build_wordspec_imperative_to_3rd():
    config = PronominalConfig(
        set_type="a", stem_type=StemType.CONSONANT, use_3rd_person_object=True
    )
    spec = build_wordspec("imperative", config, stative=True)
    assert spec.aspect == "imperative"
    assert spec.set_name == "2nd to 3rd"


def test_build_wordspec_perfective_stative():
    config = PronominalConfig(set_type="a", stem_type=StemType.CONSONANT)
    # Perfective for Set A + Stative should use Set A
    spec = build_wordspec("perfective", config, stative=True)
    assert spec.set_name == "3rd Set A"

    # Perfective for Set A + NON-Stative should use Set B
    spec = build_wordspec("perfective", config, stative=False)
    assert spec.set_name == "3rd Set B"


def test_build_wordspec_imperfective():
    config = PronominalConfig(set_type="a", stem_type=StemType.CONSONANT)
    spec = build_wordspec("imperfective", config, stative=False)
    assert spec.aspect == "imperfective"
    assert spec.set_name == "3rd Set A"
