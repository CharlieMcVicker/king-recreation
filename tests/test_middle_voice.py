from typing import Sequence, Tuple

from king_recreation.morphemes.middle_voice import MiddleVoice
from king_recreation.reconstruction import desegment


def _test_identify_and_reconstruct(
    h_grade,
    g_grade,
    expected: Sequence[Tuple[MiddleVoice, Tuple[str, str | None], bool]],
):
    result = MiddleVoice.identify_middle_voice(h_grade, g_grade, log=True)

    key_fn = lambda x: x[0].value
    res_sorted = sorted(result, key=key_fn)
    expected_sorted = sorted(expected, key=key_fn)

    assert (
        res_sorted == expected_sorted
    ), f"Expect res and expected to match\nRes: {res_sorted}\nExp: {expected_sorted}"

    # test apply
    for voice, (h_stem, g_stem), use_meta in expected:
        h_applied = (
            desegment(
                voice.apply(h_stem, is_glottal_grade=False, allow_metathesis=use_meta)
            )
            if h_stem is not None
            else None
        )
        g_applied = (
            desegment(
                voice.apply(g_stem, is_glottal_grade=True, allow_metathesis=use_meta)
            )
            if g_stem is not None
            else None
        )

        assert (h_applied, g_applied) == (
            h_grade,
            g_grade,
        ), f"Adding voice back in should recreate same forms (mv={voice}), {h_applied}|{g_applied}"


def test_match():
    _, _, cond = MiddleVoice.AL_ALI.get_form()

    # assert cond == Constraint.PRE_ASP, "constraint expected"
    assert cond.matches("khotht"), "match expected"


def test_middle_ali():
    h_grade, g_grade = ("alhsday", "alihsday")
    expected = [
        (MiddleVoice.NONE, (h_grade, g_grade), False),
        (MiddleVoice.AL_ALI, ("hsday", "hsday"), False),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_middle_ali_no_g():
    h_grade, g_grade = ("alhsday", None)
    expected = [
        (MiddleVoice.NONE, (h_grade, None), False),
        (MiddleVoice.AL_ALI, ("hsday", None), False),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_middle_alhkhot():
    h_grade, g_grade = ("alhkhotht", None)
    expected = [
        (MiddleVoice.NONE, (h_grade, None), False),
        (MiddleVoice.AL_ALI, ("hkhotht", None), False),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_middle_atalen():
    h_grade, g_grade = ("atalen", None)
    expected = [
        (MiddleVoice.NONE, (h_grade, None), False),
        (MiddleVoice.AT, ("alen", None), False),
        (MiddleVoice.ATA, ("len", None), False),
        (MiddleVoice.ATA_LONG, (":len", None), False),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_try_strip():
    stems = {
        "present": "atawhahthvh",
        "present_1sg": "atawahthvh",
        "imperfective": "atawhahthvh",
        "perfective": "atawhahthvh",
        "imperative": "atawhahthvh",
        "infinitive": "atawhahthvh",
    }

    expected = {
        "present": "whahthvh",
        "present_1sg": "wahthvh",
        "imperfective": "whahthvh",
        "perfective": "whahthvh",
        "imperative": "whahthvh",
        "infinitive": "whahthvh",
    }

    voice = MiddleVoice.ATA

    res = {k: voice.try_strip_form(form) for k, form in stems.items()}

    assert res == expected, "Expected ata to be stripped"


def test_empty_root():
    h_grade, g_grade = ("", "")
    expected = [
        (MiddleVoice.NONE, (h_grade, g_grade), False),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_empty_root_no_g():
    h_grade, g_grade = ("", None)
    expected = [
        (MiddleVoice.NONE, (h_grade, g_grade), False),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_alhino():
    h_grade, g_grade = ("alhino", "alino")
    expected = [
        (MiddleVoice.NONE, (h_grade, g_grade), False),
        (MiddleVoice.ALI, ("nho", "no"), True),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_alhino_strip():
    res = MiddleVoice.ALI.try_strip("alhino", "alino", allow_metathesis=True)
    print(res)
    _, _, con = MiddleVoice.ALI.get_form()
    assert res
    assert res[1] is not None
    assert con.matches(res[0])
    assert con.matches(res[1])


def test_hide():
    h_grade, g_grade = ("atihsgal", "atihsgal")
    expected = [
        (MiddleVoice.NONE, (h_grade, g_grade), False),
        (MiddleVoice.AT, ("ihsgal", "ihsgal"), False),
        (MiddleVoice.ATI, ("hsgal", "hsgal"), False),
        (MiddleVoice.ATI_V, ("vhsgal", "vhsgal"), False),
        (MiddleVoice.ATI_LONG, (":hsgal", ":hsgal"), False),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)
