"""
Segment-Aware Orthography & Phonology Module

Provides functionality to transform morpheme-segmented or raw strings into
community-facing orthography while preserving morpheme boundary integrity.
Specifically, explicit D+H sequences across morpheme boundaries (e.g. "d-h" or "D+H")
are preserved as "d-h" / "dh" without collapsing into aspirated "t" or "th".
"""

import re

from dictionary_pipeline.utils.text import respell_consonants

MORPHEME_BOUNDARY_MARKERS = ("-", "+", ".")


def convert_to_community_orthography(
    segmented_str: str,
    preserve_boundaries: bool = False,
    boundary_marker: str = "-",
) -> str:
    """
    Converts a segmented or raw Cherokee morphological representation to
    community-facing orthography.

    - Morpheme boundary D+H sequences (e.g. 'd-h', 'd+h', 'D-H') are preserved so that
      the 'd' and 'h' are kept distinct instead of collapsing to 't' / 'th'.
    - If preserve_boundaries is True, boundary markers are retained.
    - If preserve_boundaries is False, boundary markers are removed after phonological
      transformations have been safely applied across boundaries.
    """
    if not segmented_str:
        return ""

    # We temporarily replace boundary D+H sequences with a placeholder token that contains no d/h/t/k/g/etc.
    # or boundary chars [-+.], so it remains intact through segment splitting and consonant respelling.
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
    respelled_segments = [respell_consonants(seg) for seg in segments]

    if preserve_boundaries:
        res = boundary_marker.join(respelled_segments)
    else:
        res = "".join(respelled_segments)

    # Restore D+H boundary tokens to d-h or dh
    res = res.replace(dh_token_bound.strip(), f"d{boundary_marker}h")
    res = res.replace(dh_token_nobound.strip(), "dh")

    return res
