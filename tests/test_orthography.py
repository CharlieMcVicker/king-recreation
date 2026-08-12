from dictionary_pipeline.orthography import convert_to_community_orthography


def test_dh_morpheme_boundary_preservation_without_boundary_markers():
    """
    Ensure D+H across a morpheme boundary (e.g. 'd-h' or 'd+h') is preserved as 'dh'
    and does NOT collapse to 't' or 'th'.
    """
    # Morpheme boundary d-h
    input_str = "ad-hu"
    output = convert_to_community_orthography(input_str, preserve_boundaries=False)
    # 'ad' alone would normally become 'at' via respell_consonants ('d' -> 't'),
    # but at the boundary with 'h', 'd-h' must preserve the d+h sequence!
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
    assert output.startswith("ad-h") or output.startswith("at-h") or "d-h" in output
    # Specifically check 'd-h' sequence is preserved across boundary
    assert "d-h" in output


def test_dh_plus_boundary_marker():
    """
    Test using '+' as boundary marker.
    """
    input_str = "gad+ha"
    output = convert_to_community_orthography(input_str, preserve_boundaries=False)
    assert "dh" in output


def test_normal_consonant_respelling():
    """
    Ensure normal respelling rules (like d -> t, k -> kh, t -> th) still work when non-D+H boundaries or non-boundaries exist.
    """
    input_str = "d-ka"
    # d -> t, k -> kh
    output = convert_to_community_orthography(input_str, preserve_boundaries=False)
    assert output == "tkha" or "t" in output


def test_empty_and_plain_strings():
    assert convert_to_community_orthography("") == ""
    assert convert_to_community_orthography("da") == "ta"
