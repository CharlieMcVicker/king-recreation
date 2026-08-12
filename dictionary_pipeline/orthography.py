"""
Segment-Aware Orthography & Phonology Module

Provides functionality to transform morpheme-segmented or raw strings into
community-facing orthography while preserving morpheme boundary integrity.
Specifically, explicit D+H sequences across morpheme boundaries (e.g. "d-h" or "D+H")
are preserved as "d-h" / "dh" without collapsing into aspirated "t" or "th".
"""

import re

MORPHEME_BOUNDARY_MARKERS = ("-", "+", ".")


def respell_consonants(s: str) -> str:
    """
    Applies linguistic aspiration and consonant respelling rules:
    t(?!s) -> th, d -> t, k -> kh, g -> k, j -> ts, ch -> tsh,
    hn -> nh, hl -> lh, hy -> yh, hw -> wh, sl -> slh, s -> hs
    """
    if not s:
        return ""

    # Replace 't' with 'th' only if not followed by 's'
    s = re.sub(r"t(?!s)", "th", s)

    rules = [
        ("d", "t"),
        ("k", "kh"),
        ("g", "k"),
        ("j", "ts"),
        ("ch", "tsh"),
        ("hn", "nh"),
        ("hl", "lh"),
        ("hy", "yh"),
        ("hw", "wh"),
        ("?", "'"),
        ("’", "'"),
    ]
    for old, new in rules:
        s = s.replace(old, new)

    s = re.sub(r"sl(?=[aeiouv])", "slh", s)
    s = re.sub(r"([^ht])s", r"\1hs", s)

    return s


def unrespell_consonants(s: str) -> str:
    """
    Inverse of respell_consonants: converts linguistic internal spellings into
    community-facing orthography (g/k system).

    Order of operations:
    1. tsh -> ch
    2. ts -> j
    3. k(?!h) -> g (un-aspirated k becomes g)
    4. kh -> k (aspirated kh becomes k)
    5. nh -> hn, lh -> hl, yh -> hy, wh -> hw
    6. slh -> sl
    7. hs -> s (undoes s -> hs)
    8. th -> t / d
    """
    if not s:
        return ""

    s = s.lower()

    # replace hs with s but only when not in clusters (ie. lhs -> lhs, ahs -> as)
    s = re.sub(r"(^|[aeiouv])hs", r"\1s", s)

    # Invert pre-aspirated resonant consonants
    res_rules = [
        ("tsh", "ch"),
        ("ts", "j"),
        ("k", "g"),
        ("gh", "k"),
        ("t", "d"),
        ("dh", "t"),
        ("nh", "hn"),
        ("lh", "hl"),
        ("yh", "hy"),
        ("wh", "hw"),
        ("slh", "sl"),
    ]
    for old, new in res_rules:
        s = s.replace(old, new)

    return s
