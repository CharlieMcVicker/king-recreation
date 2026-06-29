import re


def respell_consonants(s: str) -> str:
    # Rewrite rules for aspiration marking
    # Order matters: t->th before d->t, k->kh before g->k
    # Exception: ts should stay ts (not become ths)

    # We want to replace 't' with 'th' only if it's not followed by 's'
    s = re.sub(r"t(?!s)", "th", s)

    rules = [
        # ("t", "th"), # Handled by regex above to allow for ts exception
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


def clean_string(s: str) -> str:
    if not s or s == "-----":
        return ""
    # Remove tones [1234], glottal stops [?], periods [.], and apostrophes ['’] (which are glottal stops in new source)
    # README says tone markings /[1234\.]/ and glottal stops /\?/
    s = re.sub(r"[1234\.]", "", s)
    return respell_consonants(s)
