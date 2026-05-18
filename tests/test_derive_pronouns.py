from dictionary_pipeline.dictionary_forms import Prediction
from dictionary_pipeline.phases.identify_prefixes import (
    PrefixDeriver,
    derive_pronominals,
)
from morphology.morphemes.prefixes import PronominalConfig
from morphology.morphemes.prefixes.pronominals import StemType
from morphology.morphology_types import PronominalSet


def test_angry_with_config():
    stems = {
        "present": "unhalvha",
        "present_1sg": "akhinalvha",
        "imperfective": "unhalvs",
    }
    pron_config = PronominalConfig(
        set_type=PronominalSet.SET_B,
        stem_type=StemType.CONSONANT,
        allow_h_metathesis=True,
        use_aki_for_1st_set_b=True,
    )
    res = derive_pronominals(Prediction.FULL_STATIVE, stems, pron_config, log=True)

    assert res


def test_angry():
    stems = {
        "present": "unhalv",
        "present_1sg": "akhinalv",
        "imperfective": "unhalv",
    }

    d = PrefixDeriver()
    res = d.derive_row(Prediction.FULL_STATIVE, stems, stems, log=True)
    print(res)
    assert len(res)
