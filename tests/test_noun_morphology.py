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
    get_noun_wordspec,
)


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
    spec_root = get_noun_wordspec(NounStructure.ROOT)
    forms_root = engine.reconstruct_spec(verb, spec_root)
    assert "ni" in forms_root

    # 2. Agentive Noun
    spec_agentive = get_noun_wordspec(
        NounStructure.AGENTIVE,
        person=Person.FIRST,
        number=Number.SINGULAR,
        pronominal_set=PronominalSet.SET_A,
    )
    forms_agentive = engine.reconstruct_spec(verb, spec_agentive)
    assert "tsi-ni-ahsk-i" in forms_agentive

    # 3. Completive Noun
    spec_completive = get_noun_wordspec(NounStructure.COMPLETIVE)
    forms_completive = engine.reconstruct_spec(verb, spec_completive)
    assert "ni-v'i" in forms_completive

    # 4. Incompletive Noun
    spec_incompletive = get_noun_wordspec(NounStructure.INCOMPLETIVE)
    forms_incompletive = engine.reconstruct_spec(verb, spec_incompletive)
    assert "ni-ahsk-v'i" in forms_incompletive


def test_get_noun_wordspec():
    from morphology.word_spec import SyntacticCategory

    # Root Noun mapping verification
    spec_root = get_noun_wordspec(NounStructure.ROOT)
    assert spec_root.syntactic_category == SyntacticCategory.NOMINAL
    assert spec_root.aspect is None
    assert spec_root.tense_ending == ""

    # Agentive Noun mapping verification
    spec_agentive = get_noun_wordspec(NounStructure.AGENTIVE)
    assert spec_agentive.syntactic_category == SyntacticCategory.NOMINAL
    assert spec_agentive.aspect == Aspect.IMPERFECTIVE
    assert spec_agentive.tense_ending == "i"

    # Completive Noun mapping verification
    spec_completive = get_noun_wordspec(NounStructure.COMPLETIVE)
    assert spec_completive.syntactic_category == SyntacticCategory.VERBY
    assert spec_completive.aspect == Aspect.PERFECTIVE
    assert spec_completive.tense_ending == "v'i"

    # Incompletive Noun mapping verification
    spec_incompletive = get_noun_wordspec(NounStructure.INCOMPLETIVE)
    assert spec_incompletive.syntactic_category == SyntacticCategory.VERBY
    assert spec_incompletive.aspect == Aspect.IMPERFECTIVE
    assert spec_incompletive.tense_ending == "v'i"



