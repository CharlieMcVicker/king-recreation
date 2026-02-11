import pytest

from king_recreation.tone.analysis import (
    check_prediction,
    generate_underlying_forms,
    predict_h1_for_form,
)
from king_recreation.tone.models import (
    Environment,
    GlottalPosition,
    H1Config,
    LexedForm,
    Tonicity,
)


def _test_case(test_str, expected, log=False):
    inferences = predict_h1_for_form(test_str)
    if log:
        for v, infs in inferences:
            print(f"Vowel: {v.quality}")
            for inf in infs:
                print(f"  {inf}")
    assert len(inferences) == len(
        expected
    ), f"Number of vowels with H1 mismatch for {test_str}. Got {len(inferences)}, expected {len(expected)}"

    for i, ((v, inf), exp_list) in enumerate(zip(inferences, expected)):
        assert set(inf) == set(
            exp_list
        ), f"Possibilities mismatch for vowel {i} ({v.quality}) in {test_str}"


def test_2_32():
    _test_case(
        test_str="a2la32hs",
        expected=[
            [
                H1Config(
                    historically_long=False,
                    glottal_position=GlottalPosition.PRE_C,
                    env=Environment.NO_SPREAD,
                ),
            ]
        ],
    )


def test_23_32():
    _test_case(
        test_str="i23nv32hs",
        expected=[
            [
                H1Config(
                    historically_long=True,
                    glottal_position=GlottalPosition.PRE_C,
                    env=Environment.SPREAD,
                ),
                H1Config(
                    historically_long=False,
                    glottal_position=GlottalPosition.PRE_C,
                    env=Environment.SPREAD,
                ),
            ]
        ],
    )


def test_surface_glottal_post_c():
    _test_case(
        test_str="ga3'la",
        expected=[
            [
                H1Config(
                    historically_long=False,
                    glottal_position=GlottalPosition.POST_C,
                    env=Environment.NO_SPREAD,
                ),
            ]
        ],
        log=True,
    )


def test_spreading_blocked_short():
    _test_case(
        test_str="nu33the22yo32l",
        expected=[
            [
                H1Config(
                    historically_long=True,
                    glottal_position=GlottalPosition.POST_C,
                    env=Environment.NO_SPREAD,
                ),
                H1Config(
                    historically_long=True,
                    glottal_position=GlottalPosition.PRE_C,
                    env=Environment.NO_SPREAD,
                ),
            ],
            [
                H1Config(
                    historically_long=False,
                    glottal_position=GlottalPosition.PRE_C,
                    env=Environment.NO_SPREAD,
                ),
            ],
        ],
        log=True,
    )


def test_spreading_blocked_long():
    _test_case(
        test_str="ga3'li22do33ha2",
        expected=[
            [
                H1Config(
                    historically_long=False,
                    glottal_position=GlottalPosition.POST_C,
                    env=Environment.NO_SPREAD,
                ),
            ],
            [
                H1Config(
                    historically_long=True,
                    glottal_position=GlottalPosition.PRE_C,
                    env=Environment.NO_SPREAD,
                ),
                H1Config(
                    historically_long=True,
                    glottal_position=GlottalPosition.POST_C,
                    env=Environment.NO_SPREAD,
                ),
                H1Config(
                    historically_long=True,
                    glottal_position=GlottalPosition.POST_C,
                    env=Environment.SPREAD,
                ),
            ],
        ],
        log=True,
    )


def test_h2_short_next():
    # a/ followed by short la -> a3la
    # next is short, so H2 becomes 3 and does NOT block H1 on following syllables.
    assert check_prediction("a/la", "a3la2")
    assert not check_prediction("a/la", "a3la3")


def test_h2_long_next():
    # aa/ followed by long laa -> aa33laa
    # next is long, so H2 becomes 33 and DOES block H1 on following syllables.
    assert check_prediction("aa/laa'", "a33la2'")


def test_h2_parsing():
    lf = LexedForm.from_str("ga/li")
    # tokens: [Consonant(g), HistoricalVowel(a, h2=True), Consonant(l), HistoricalVowel(i)]
    assert lf.tokens[1].h2
    assert str(lf) == "ga/li"


def test_h2_brute_force_generation():
    # Test that generate_underlying_forms finds H2
    candidates = generate_underlying_forms("a3-la3")
    underlying_strs = [str(c) for c in candidates]
    assert "a/-la" in underlying_strs

    candidates_long = generate_underlying_forms("a23-la33")
    underlying_strs_long = [str(c) for c in candidates_long]
    # aa/ because surface is 33 (long)
    assert "aa/-laa" in underlying_strs_long


# def test_h2_no_33():
#     # h2 produces
#     candidates = generate_underlying_forms("t-e33h")
#     underlying_strs = [str(c) for c in candidates]
#     assert "t-ee/h" not in underlying_strs


def test_h2_23_33():
    candidates = generate_underlying_forms("ka2ne23tl-i33y-v2'-a")
    underlying_strs = [str(c) for c in candidates]
    assert "kanee/tl-iiy-vv'-a" in underlying_strs


def test_infinitive_environment_override():
    # Detect 'lf' (21) tone on short vowel.
    # In NO_SPREAD env (default for start of word), 'lf' is not valid for H1.
    # In BLOCKED env, 'lf' IS valid.

    test_str = "a21-ta"

    # CASE 1: Not infinitive -> No Spread -> No match for lf
    results_normal = predict_h1_for_form(test_str, tonicity=Tonicity.TONIC)
    assert (
        len(results_normal) == 0
    ), "Should not find H1 candidates for 'a21' (PRE_C) in NO_SPREAD env"

    # CASE 2: Infinitive -> Blocked -> Match for lf
    results_inf = predict_h1_for_form(test_str, tonicity=Tonicity.INFINITIVE)
    assert (
        len(results_inf) > 0
    ), "Should find H1 candidates for 'a21' (PRE_C) in infinitive (BLOCKED) env"

    # Validate specifically that we got BLOCKED environment configs
    for v, configs in results_inf:
        for cfg in configs:
            assert cfg.env == Environment.BLOCKED


def test_atonic_environment():
    # ATONIC should always be BLOCKED
    test_str = "a21-ta"
    results = predict_h1_for_form(test_str, tonicity=Tonicity.ATONIC)
    assert len(results) > 0
    for v, configs in results:
        for cfg in configs:
            assert cfg.env == Environment.BLOCKED
