from morphology.morphology_types import Aspect, Number, Person, PronominalSet
from morphology.word_spec import SyntacticCategory
from noun_pipeline.phases.generate_hypotheses import generate_hypotheses


def test_generate_hypotheses_ambiguous_suffix():
    # 'uwayeli' could be parsed as:
    # 1. ROOT 'uwayeli'
    # 2. AGENTIVE 'uwayel' + 'i'
    # Plus, 'u' is a 3rd person singular prefix for Set B.

    hypotheses = generate_hypotheses("uwayeli")

    assert len(hypotheses) > 0

    # Let's check some of the expected hypotheses
    root_forms = [
        h
        for h in hypotheses
        if h.word_spec.syntactic_category == SyntacticCategory.NOMINAL
        and h.word_spec.aspect is None
    ]
    agentive_forms = [
        h
        for h in hypotheses
        if h.word_spec.syntactic_category == SyntacticCategory.NOMINAL
        and h.word_spec.aspect == Aspect.IMPERFECTIVE
    ]

    assert len(root_forms) >= 1
    assert len(agentive_forms) >= 1

    # Expect unstripped forms
    assert any(h.stem == "uwayeli" and h.word_spec.person is None for h in root_forms)
    assert any(
        h.stem == "uwayel" and h.word_spec.person is None for h in agentive_forms
    )


def test_generate_hypotheses_pronominal_stripping():
    # 'uweni' starts with 'uw' which is a variant of 'u' (Set B 3rd Singular) on a vowel stem (like 'e' or 'a' or 'v')
    # Or could be stripped as 'u' prefix on 'weni' (if weni is a consonant stem).
    hypotheses = generate_hypotheses("uweni")

    assert len(hypotheses) > 0

    stripped_forms = [
        h
        for h in hypotheses
        if h.word_spec.person == Person.THIRD
        and h.word_spec.number == Number.SINGULAR
        and h.word_spec.pronominal_set == PronominalSet.SET_B
    ]

    assert len(stripped_forms) > 0
    # One of the stems could be 'eni' (since 'uw' + 'e' -> 'uwe' -> 'uweni')
    assert any(h.stem == "eni" or h.stem == "weni" for h in stripped_forms)


def test_generate_hypotheses_ani_prefix():
    # 'anigili' starts with 'ani' (Set A 3rd Plural)
    hypotheses = generate_hypotheses("anigili")

    ani_stripped = [
        h
        for h in hypotheses
        if h.word_spec.person == Person.THIRD
        and h.word_spec.number == Number.PLURAL
        and h.word_spec.pronominal_set == PronominalSet.SET_A
    ]

    assert len(ani_stripped) > 0
    assert any(h.stem == "gili" or h.stem == "gil" for h in ani_stripped)
