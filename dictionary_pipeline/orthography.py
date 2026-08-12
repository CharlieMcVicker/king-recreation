"""
Segment-Aware Orthography & Phonology Module

Provides functionality to transform morpheme-segmented or raw strings into
community-facing orthography while preserving morpheme boundary integrity.
Specifically, explicit D+H sequences across morpheme boundaries (e.g. "d-h" or "D+H")
are preserved as "d-h" / "dh" without collapsing into aspirated "t" or "th".
"""

import re
from typing import Sequence

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

    s = s.replace("tsh", "ch").replace("Tsh", "Ch").replace("TSH", "CH")
    s = s.replace("ts", "j").replace("Ts", "J").replace("TS", "J")

    # Step 3 & 4: k(?!h) -> g, kh -> k using context-free regexes
    s = re.sub(r"k(?!h)", "g", s)
    s = re.sub(r"K(?!h)", "G", s)
    s = re.sub(r"kh", "k", s)
    s = re.sub(r"Kh", "K", s)
    s = re.sub(r"KH", "K", s)

    # Invert pre-aspirated resonant consonants
    res_rules = [
        ("nh", "hn"),
        ("lh", "hl"),
        ("yh", "hy"),
        ("wh", "hw"),
        ("slh", "sl"),
        ("hs", "s"),
    ]
    for old, new in res_rules:
        s = s.replace(old, new)

    return s


def convert_segment_to_community_orthography(
    seg: str | Sequence[str],
) -> str | list[str]:
    """
    Accepts a plain segment string or list of plain segment strings (without raw boundary markers)
    and converts them to community-facing orthography.
    """
    if isinstance(seg, (list, tuple)):
        return [unrespell_consonants(s) for s in seg]
    return unrespell_consonants(str(seg))


def convert_to_community_orthography(
    segmented_str: str,
    preserve_boundaries: bool = False,
    boundary_marker: str = "-",
) -> str:
    """
    Converts a segmented or raw Cherokee morphological representation to
    community-facing orthography (g/k system).
    """
    if not segmented_str:
        return ""

    dh_token_bound = " ZZZDHBOUNDZZZ "
    dh_token_nobound = " ZZZDHNOBOUNDZZZ "

    dh_regex = re.compile(r"([dD])\s*[-+.]+\s*([hH])")

    def _replace_dh(match: re.Match[str]) -> str:
        if preserve_boundaries:
            return dh_token_bound
        else:
            return dh_token_nobound

    processed = dh_regex.sub(_replace_dh, segmented_str)

    # Split segments by boundary markers [-+.]
    segments = re.split(r"[-+.]+", processed)
    respelled_segments = [unrespell_consonants(seg) for seg in segments]

    if preserve_boundaries:
        res = boundary_marker.join(respelled_segments)
    else:
        res = "".join(respelled_segments)

    # Restore D+H boundary tokens to d-h or dh
    res = res.replace(dh_token_bound.strip(), f"d{boundary_marker}h")
    res = res.replace(dh_token_nobound.strip(), "dh")

    return res
