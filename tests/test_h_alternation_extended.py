
from king_recreation.h_alternation import _drop_first_h
from king_recreation.phases.identify_prefixes import is_strict_compatible


def test_blinking_vowel_restoration():
    """
    Test 'he's closing his eyes' (blinking).
    Target (3rd): akhthastih (has h)
    Stem (1st): akathastih (h dropped, a restored)
    """
    target = "akhthastih"
    stem_1sg = "akathastih"

    # Current behavior:
    dropped = _drop_first_h(target)  # akthastih
    assert dropped == "akthastih"

    # Strict check fails
    assert not is_strict_compatible(stem_1sg, dropped)


def test_dancing_vowel_restoration():
    """
    Test 'he's dancing'.
    Target (3rd): alski (no explicit h, but acts syncopated)
    Stem (1st): aliski (vowel restored)
    """
    target = "alski"
    stem_1sg = "aliski"

    dropped = _drop_first_h(target)  # alski (no h to drop)
    assert dropped == "alski"

    # Strict check fails
    assert not is_strict_compatible(stem_1sg, dropped)
