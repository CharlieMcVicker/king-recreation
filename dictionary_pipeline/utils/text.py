import re

from dictionary_pipeline.orthography import respell_consonants


def clean_string(s: str) -> str:
    if not s or s == "-----":
        return ""
    # Remove tones [1234], glottal stops [?], periods [.], and apostrophes ['’] (which are glottal stops in new source)
    # README says tone markings /[1234\.]/ and glottal stops /\?/
    s = re.sub(r"[1234\.]", "", s)
    return respell_consonants(s)
