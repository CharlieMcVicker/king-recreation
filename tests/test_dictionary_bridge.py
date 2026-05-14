from dictionary_pipeline.dictionary_forms import build_wordspec, get_form_spec
from morphology.morphemes.prefixes.pronominals import PronominalConfig, StemType
from morphology.word_spec import Aspect, Number, Person, PronominalSet


def test_get_form_spec():
    # Present
    spec = get_form_spec("present")
    assert spec.aspect == Aspect.PRESENT
    assert spec.person == Person.THIRD
    assert spec.allow_set_a == True

    # Perfective
    spec = get_form_spec("perfective")
    assert spec.aspect == Aspect.PERFECTIVE
    assert spec.person == Person.THIRD
    assert spec.allow_set_a == False

    # 1sg
    spec = get_form_spec("present_1sg")
    assert spec.aspect == Aspect.PRESENT
    assert spec.person == Person.FIRST
    assert spec.allow_set_a == True


def test_build_wordspec():
    config = PronominalConfig(
        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
    )

    # 3rd Present Set A
    ws = build_wordspec("present", config, False)
    assert ws.aspect == Aspect.PRESENT
    assert ws.person == Person.THIRD
    assert ws.number == Number.SINGULAR
    assert ws.pronominal_set == PronominalSet.SET_A

    # 3rd Perfective Set B (forced)
    ws = build_wordspec("perfective", config, False)
    assert ws.aspect == Aspect.PERFECTIVE
    assert ws.person == Person.THIRD
    assert ws.number == Number.SINGULAR
    assert ws.pronominal_set == PronominalSet.SET_B
