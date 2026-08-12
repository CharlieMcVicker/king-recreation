from dictionary_pipeline.orthography import (
    convert_segment_to_community_orthography,
    convert_to_community_orthography,
    respell_consonants,
    unrespell_consonants,
)


def test_respell_consonants_location():
    """
    Verify respell_consonants is housed in orthography.py and works as expected.
    """
    assert respell_consonants("ka") == "kha"
    assert respell_consonants("ga") == "ka"
    assert respell_consonants("asa") == "ahsa"
    assert respell_consonants("cha") == "tsha"
    assert respell_consonants("ja") == "tsa"
    assert respell_consonants("hna") == "nha"


def test_unrespell_consonants_inverse_pairs():
    """
    Verify unrespell_consonants properly inverts respell_consonants to Community Orthography (g/k system).
    Rules:
    - k(?!h) -> g (un-aspirated k becomes g)
    - kh -> k (aspirated kh becomes k)
    - hs -> s (undoes s -> hs)
    - tsh -> ch, ts -> j
    - nh -> hn, lh -> hl, yh -> hy, wh -> hw
    """
    # Plain k -> g
    assert unrespell_consonants("ka") == "ga"
    # Aspirated kh -> k
    assert unrespell_consonants("kha") == "ka"
    # Pre-aspirated hs -> s
    assert unrespell_consonants("hsa") == "sa"
    # Pre-aspirated ts / tsh -> j / ch
    assert unrespell_consonants("tsa") == "ja"
    assert unrespell_consonants("tsha") == "cha"
    # Pre-aspirated resonants
    assert unrespell_consonants("nha") == "hna"
    assert unrespell_consonants("lha") == "hla"
    assert unrespell_consonants("yha") == "hya"
    assert unrespell_consonants("wha") == "hwa"


def test_convert_segment_to_community_orthography_plain():
    """
    Test convert_segment_to_community_orthography on single plain segment strings and lists of segments.
    """
    assert convert_segment_to_community_orthography("kha") == "ka"
    assert convert_segment_to_community_orthography("ka") == "ga"

    segments = ["kha", "nel", "a"]
    converted = convert_segment_to_community_orthography(segments)
    assert converted == ["ka", "nel", "a"]


def test_dh_morpheme_boundary_preservation_without_boundary_markers():
    """
    Ensure D+H across a morpheme boundary (e.g. 'd-h' or 'd+h') is preserved as 'dh'
    and does NOT collapse to 't' or 'th'.
    """
    input_str = "ad-hu"
    output = convert_to_community_orthography(input_str, preserve_boundaries=False)
    assert "dh" in output
    assert not output.startswith("ath")
    assert not output.startswith("th")


def test_dh_morpheme_boundary_preservation_with_boundary_markers():
    """
    Ensure D+H across a morpheme boundary retains boundary marker when requested.
    """
    input_str = "ad-hda"
    output = convert_to_community_orthography(
        input_str, preserve_boundaries=True, boundary_marker="-"
    )
    assert "d-h" in output or "dh" in output


def test_dh_plus_boundary_marker():
    """
    Test using '+' as boundary marker.
    """
    input_str = "gad+ha"
    output = convert_to_community_orthography(input_str, preserve_boundaries=False)
    assert "dh" in output


def test_empty_and_plain_strings():
    assert convert_to_community_orthography("") == ""
    assert convert_segment_to_community_orthography("") == ""
