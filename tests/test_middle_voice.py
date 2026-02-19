from typing import List, Tuple

from king_recreation.morphemes.middle_voice import MiddleVoice
from king_recreation.reconstruction import desegment


def _test_identify_and_reconstruct(
    h_grade, g_grade, expected: List[Tuple[MiddleVoice, Tuple[str, str | None]]]
):
    result = MiddleVoice.identify_middle_voice(h_grade, g_grade)

    assert sorted([(v[0], v[1]) for v in result], key=lambda x: x[0].value) == sorted(
        expected, key=lambda x: x[0].value
    )

    # test apply
    for voice, (h_stem, g_stem) in expected:
        h_applied = (
            desegment(
                voice.apply(h_stem, is_glottal_grade=False, allow_metathesis=False)
            )
            if h_stem is not None
            else None
        )
        g_applied = (
            desegment(
                voice.apply(g_stem, is_glottal_grade=True, allow_metathesis=False)
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
        (MiddleVoice.NONE, (h_grade, g_grade)),
        (MiddleVoice.AL_ALI, ("hsday", "hsday")),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_middle_ali_no_g():
    h_grade, g_grade = ("alhsday", None)
    expected = [
        (MiddleVoice.NONE, (h_grade, None)),
        (MiddleVoice.AL_ALI, ("hsday", None)),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_middle_alhkhot():
    h_grade, g_grade = ("alhkhotht", None)
    expected = [
        (MiddleVoice.NONE, (h_grade, None)),
        (MiddleVoice.AL_ALI, ("hkhotht", None)),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_middle_atalen():
    h_grade, g_grade = ("atalen", None)
    expected = [
        (MiddleVoice.NONE, (h_grade, None)),
        (MiddleVoice.AT, ("alen", None)),
        (MiddleVoice.ATA, ("len", None)),
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
        (MiddleVoice.NONE, (h_grade, g_grade)),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)


def test_empty_root_no_g():
    h_grade, g_grade = ("", None)
    expected = [
        (MiddleVoice.NONE, (h_grade, g_grade)),
    ]
    _test_identify_and_reconstruct(h_grade, g_grade, expected)
