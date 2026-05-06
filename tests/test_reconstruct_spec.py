from king_recreation.morphemes.prefixes import PrefixConfig
from king_recreation.morphemes.prefixes.prepronominals import PrePronominalConfig
from king_recreation.morphemes.prefixes.pronominals import PronominalConfig, StemType
from king_recreation.reconstruction import ReconstructableVerb, ReconstructionEngine
from king_recreation.word_spec import Aspect, Number, Person, PronominalSet, WordSpec


def test_reconstruct_spec():
    # Setup engine
    engine = ReconstructionEngine("data/classes.csv")

    # Create a verb (simplified for testing)
    verb = ReconstructableVerb(
        definition="it is happening",
        h_grade_root="ni",
        glottal_grade_root="ni",  # Same for this example
        post_root_morpheme=None,
        class_name="a",  # class 'a' in classes.csv
        config=PrefixConfig(
            pre=PrePronominalConfig(),
            pron=PronominalConfig(
                set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
            ),
            stative=False,
        ),
    )

    # Test case: 1st person prefix + present aspect
    spec = WordSpec(
        aspect=Aspect.PRESENT,
        person=Person.FIRST,
        number=Number.SINGULAR,
        pronominal_set=PronominalSet.SET_A,
        stative=False,
    )

    forms = engine.reconstruct_spec(verb, spec)

    # "tsi" + "ni" + "a'" -> "tsi-ni-a'"
    assert "tsi-ni-a'" in forms

    # Test case: 3rd person plural prefix + perfective aspect
    spec = WordSpec(
        aspect=Aspect.PERFECTIVE,
        person=Person.THIRD,
        number=Number.PLURAL,
        pronominal_set=PronominalSet.SET_B,
        stative=False,
    )
    forms = engine.reconstruct_spec(verb, spec)

    assert "uni-ni-" in forms
