import pytest

from king_recreation.preprocess_ced import clean_row, clean_string, respell_consonants


def test_clean_string():
    # da1li23yo3hi.2a -> daliyohia -> taliyohia
    assert clean_string("da1li23yo3hi.2a") == "taliyohia"
    # u1ja.3?i1sv23?i -> ujaisvi -> utsaisvi
    assert clean_string("u1ja.3?i1sv23?i") == "utsaisvi"
    assert clean_string("-----") == ""
    assert clean_string("") == ""
    assert clean_string(None) == ""


def test_respell_consonants():
    # t -> th
    assert respell_consonants("ta") == "tha"
    # d -> t
    assert respell_consonants("da") == "ta"
    # k -> kh
    assert respell_consonants("ka") == "kha"
    # g -> k
    assert respell_consonants("ga") == "ka"
    # complex
    assert respell_consonants("tadig") == "thatik"
    # ts exception
    assert respell_consonants("atsa") == "atsa"
    assert respell_consonants("tsa") == "tsa"

    # hl -> lh | _ C
    assert respell_consonants("hla") == "hla"  # followed by vowel, no change
    assert (
        respell_consonants("hlta") == "lhtha"
    )  # followed by consonant (t->th), change

    # hn -> nh | _ C
    assert respell_consonants("hna") == "hna"  # followed by vowel, no change
    assert (
        respell_consonants("hnta") == "nhtha"
    )  # followed by consonant (t->th), change


def test_clean_row_basic():
    row = {
        "definition": "he's putting on his socks",
        "3rd present": "da1li23yo3hi.2a",  # taliyohia -> taliyohi
        "3rd incompletive habitual": "da1li23yo3hi.2ho3?i",  # taliyohihoi -> taliyohih
        "3rd completive past": "du1li23yo3hlv23?i",  # tuliyohlvi -> tuliyohl
        "2nd imperative": "ta2li3yo2ga",  # thaliyoka
        "3rd infinitive": "ju2li23yo3sdi",  # juliyosti -> juliyost
    }
    cleaned = clean_row(row)
    assert cleaned["definition"] == "he's putting on his socks"
    assert cleaned["present"] == "taliyohi"
    assert cleaned["imperfective"] == "taliyohih"
    assert cleaned["perfective"] == "tuliyohl"
    assert cleaned["imperative"] == "thaliyoka"
    assert cleaned["infinitive"] == "tsuliyost"


def test_clean_row_missing():
    row = {
        "definition": "it's ending",
        "3rd present": "al1sgwa.2di.3?a",
        "3rd incompletive habitual": "al1sgwa.2di32sgo3?i",
        "3rd completive past": "ul1sgwa.3dv23?i",
        "2nd imperative": "-----",
        "3rd infinitive": "ul2sgwa.2di1sdi",
    }
    cleaned = clean_row(row)
    assert cleaned["imperative"] == ""
    assert cleaned["perfective"] == "ulskwat"  # ulskwadvi -> ulskwat


def test_present_vowel_stripping():
    # Case: ends in 'a'
    row_a = {"3rd present": "ga1lo1e.2ga"}  # galoega -> kaloeka -> kaloek
    assert clean_row(row_a)["present"] == "kaloek"

    # Case: ends in 'i'
    row_i = {"3rd present": "a1ki1?a"}  # akia -> akhia -> akhi (ends in ia)
    assert clean_row(row_i)["present"] == "akhi"

    # Case: ends in 'i' but not 'ia'
    row_single_i = {"3rd present": "u1wa1si"}  # uwasi -> uwas
    assert clean_row(row_single_i)["present"] == "uwas"

    # Case: ends in 'ia'
    row_ia = {"3rd present": "da1li23yo3hi.2a"}  # daliyohia -> taliyohia -> taliyohi
    assert clean_row(row_ia)["present"] == "taliyohi"
