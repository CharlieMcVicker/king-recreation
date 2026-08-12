from dictionary_pipeline.orthography import respell_consonants, unrespell_consonants


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
    assert unrespell_consonants("ahs") == "as"
    # Pre-aspirated ts / tsh -> j / ch
    assert unrespell_consonants("tsa") == "ja"
    assert unrespell_consonants("tsha") == "cha"
    # Pre-aspirated resonants
    assert unrespell_consonants("nha") == "hna"
    assert unrespell_consonants("lha") == "hla"
    assert unrespell_consonants("yha") == "hya"
    assert unrespell_consonants("wha") == "hwa"
