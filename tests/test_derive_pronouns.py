from king_recreation.morphemes.prefixes import PronominalConfig
from king_recreation.morphemes.prefixes.pronominals import StemType
from king_recreation.phases.identify_prefixes import PrefixDeriver, derive_pronominals


def test_angry_with_config():
    stems = {
        "present": "unhalvha",
        "present_1sg": "akhinalvha",
        "imperfective": "unhalvs",
    }
    pron_config = PronominalConfig(
        set_type="b",
        stem_type=StemType.CONSONANT,
        allow_h_metathesis=True,
        use_aki_for_1st_set_b=True,
    )
    res = derive_pronominals(stems, pron_config, stative=True, log=True)

    assert res


def test_angry():
    stems = {
        "present": "unhalv",
        "present_1sg": "akhinalv",
        "imperfective": "unhalv",
    }

    d = PrefixDeriver()
    res = d.derive_row(stems, stems, log=True)
    print(res)
    assert len(res)
