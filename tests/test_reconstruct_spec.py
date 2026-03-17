from king_recreation.morphemes.prefixes import PrefixConfig
from king_recreation.morphemes.prefixes.prepronominals import PrePronominalConfig
from king_recreation.morphemes.prefixes.pronominals import PronominalConfig, StemType
from king_recreation.reconstruction import ReconstructableVerb, ReconstructionEngine
from king_recreation.word_spec import WordSpec


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
            pron=PronominalConfig(set_type="a", stem_type=StemType.CONSONANT),
            stative=False,
        ),
    )

    # Test case: 1st person prefix + present aspect
    spec = WordSpec(aspect="present", set_name="1st Set A", stative=False)

    forms = engine.reconstruct_spec(verb, spec)

    # "tsi" + "ni" + "a'" -> "tsi-ni-a'"
    assert "tsi-ni-a'" in forms

    # Test case: 3rd person plural prefix + perfective aspect
    spec = WordSpec(aspect="perfective", set_name="3pl Set B", stative=False)
    forms = engine.reconstruct_spec(verb, spec)

    # "uni" + "ni" + "" -> "uni-ni-"
    # Looking at data/classes.csv for class 'a': perfective suffix is empty?
    # line 2: a,,,a',ahsk,,a,ahst -> aspect columns: present=a', imperfective=ahsk, perfective="", imperative=a, infinitive=ahst
    # Wait, my columns in build_wordspec mapping:
    # present -> present
    # present_1sg -> present
    # perfective -> perfective

    # Let's check exactly what the suffix is for "perfective" in class 'a'
    # Row 2: a,,,a',ahsk,,a,ahst
    # Col 4: present = a'
    # Col 5: imperfective = ahsk
    # Col 6: perfective = (empty string)
    # Col 7: imperative = a
    # Col 8: infinitive = ahst

    assert "uni-ni-" in forms
