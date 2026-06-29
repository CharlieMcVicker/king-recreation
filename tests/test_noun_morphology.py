from morphology.morphemes.prefixes import PrefixConfig
from morphology.morphemes.prefixes.prepronominals import PrePronominalConfig
from morphology.morphemes.prefixes.pronominals import PronominalConfig, StemType
from morphology.reconstruction import MorphologicalVerb, ReconstructionEngine
from morphology.word_spec import (
    Aspect,
    NounStructure,
    Number,
    Person,
    PronominalSet,
    WordSpec,
)


def test_noun_spec_properties():
    # Test ROOT structure properties
    spec_root = WordSpec(noun_structure=NounStructure.ROOT)
    assert spec_root.noun_suffix == ""
    assert spec_root.noun_aspect is None

    # Test AGENTIVE structure properties
    spec_agentive = WordSpec(noun_structure=NounStructure.AGENTIVE)
    assert spec_agentive.noun_suffix == "i"
    assert spec_agentive.noun_aspect == Aspect.IMPERFECTIVE

    # Test COMPLETIVE structure properties
    spec_completive = WordSpec(noun_structure=NounStructure.COMPLETIVE)
    assert spec_completive.noun_suffix == "v'i"
    assert spec_completive.noun_aspect == Aspect.PERFECTIVE

    # Test INCOMPLETIVE structure properties
    spec_incompletive = WordSpec(noun_structure=NounStructure.INCOMPLETIVE)
    assert spec_incompletive.noun_suffix == "o'i"
    assert spec_incompletive.noun_aspect == Aspect.IMPERFECTIVE


def test_noun_reconstruction():
    engine = ReconstructionEngine("data/classes.csv")

    # Create a MorphologicalVerb
    verb = MorphologicalVerb(
        h_grade_root="ni",
        glottal_grade_root="ni",
        post_root_morpheme=None,
        class_name="a",
        config=PrefixConfig(
            pre=PrePronominalConfig(),
            pron=PronominalConfig(
                set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
            ),
        ),
    )

    # 1. Bare Root Noun (unprefixed)
    spec_root = WordSpec(noun_structure=NounStructure.ROOT)
    forms_root = engine.reconstruct_spec(verb, spec_root)
    assert "ni" in forms_root

    # 2. Agentive Noun
    spec_agentive = WordSpec(
        noun_structure=NounStructure.AGENTIVE,
        person=Person.FIRST,
        number=Number.SINGULAR,
        pronominal_set=PronominalSet.SET_A,
    )
    forms_agentive = engine.reconstruct_spec(verb, spec_agentive)
    assert "tsi-ni-ahsk-i" in forms_agentive

    # 3. Completive Noun
    spec_completive = WordSpec(noun_structure=NounStructure.COMPLETIVE)
    forms_completive = engine.reconstruct_spec(verb, spec_completive)
    assert "ni-v'i" in forms_completive

    # 4. Incompletive Noun
    spec_incompletive = WordSpec(noun_structure=NounStructure.INCOMPLETIVE)
    forms_incompletive = engine.reconstruct_spec(verb, spec_incompletive)
    assert "ni-ahsk-o'i" in forms_incompletive
