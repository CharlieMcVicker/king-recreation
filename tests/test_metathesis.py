from morphology.metathesis import demetathesize_h, metathesize_h


def _metathesis_case(pro_form, stem, expected):
    res = metathesize_h(pro_form, stem)
    res_joined = "-".join(res)
    assert (
        res_joined == expected
    ), f"metathesis failed, expected `{expected}` got `{res_joined}`"

    surface_expected = expected.replace("-", "")
    res_stem = demetathesize_h(pro_form, joined=surface_expected)
    assert res_stem == stem, f"expected `{stem}` got `{res_stem}`"


def test_metathesize_pre_c_h():
    _metathesis_case(pro_form="ka", stem="nhoki", expected="kha-noki")


def test_metathesize_pre_v_c_h():
    _metathesis_case(pro_form="k", stem="elh", expected="kh-el")


def test_breathing_set_a():
    _metathesis_case("ka", "wholat", "kha-wolat")


def test_angry():
    base = "nhalv"
    cases = [
        (
            "aki",
            "akhi-nalv",
        ),
        (
            "tsa",
            "tsha-nalv",
        ),
    ]
    for pro, expected in cases:
        _metathesis_case(pro, base, expected)
