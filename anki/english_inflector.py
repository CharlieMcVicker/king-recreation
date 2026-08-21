"""
English semantic tense/aspect inflector for Cherokee verb definitions.

Transforms dictionary glosses (CED present progressive) into accurate English
tense/aspect/mood forms matching Cherokee inflectional categories:
- present: Present progressive (or simple present for stative verbs)
- imperfective: Habitual simple present (or with '(habitually)' for statives)
- perfective: Simple past (completive)
- present_1sg: 1st person singular present ("I ...")
- imperative: 2nd person command ("...!")
- infinitive: "(for her/it/them) to ..."
"""

from __future__ import annotations

import re
import warnings
from typing import Any

# Filter the VisibleDeprecationWarning from lemminflect's DataContainer with NumPy 2+
warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    module="lemminflect",
)
warnings.filterwarnings(
    "ignore",
    message=r".*align should be passed as Python or NumPy boolean.*",
)

import lemminflect
from lemminflect import getInflection, getLemma


def normalize_definition(raw_def: str) -> str:
    """Normalizes encoding quirks, curly apostrophes, and spaces."""
    d = raw_def
    for char in [
        chr(8217),
        chr(8216),
        chr(8218),
        chr(8219),
        "’",
        "‘",
        "`",
        "\ufffd",
    ]:
        d = d.replace(char, "'")
    return d.strip()


def clean_pronouns(text: str, target_person: str = "3rd_she") -> str:
    """
    Substitutes reflexive and object pronouns based on target person:
    - '3rd_she': himself/herself -> herself, him/her -> her, his/her -> her, he/she -> she
    - '1st': himself/herself/herself -> myself, his/her -> my, he/she -> I
    - '2nd': himself/herself/herself -> yourself, his/her -> your, he/she -> you
    """
    res = text
    if target_person == "3rd_she":
        res = re.sub(
            r"\bhimself/herself\b", "herself", res, flags=re.IGNORECASE
        )
        res = re.sub(r"\bhim/her\b", "her", res, flags=re.IGNORECASE)
        res = re.sub(r"\bhis/her\b", "her", res, flags=re.IGNORECASE)
        res = re.sub(r"\bhe/she\b", "she", res, flags=re.IGNORECASE)
        res = re.sub(r"\bhimself\b", "herself", res, flags=re.IGNORECASE)
        res = re.sub(r"\bto him\b", "to her", res, flags=re.IGNORECASE)
        res = re.sub(r"\bwith him\b", "with her", res, flags=re.IGNORECASE)
    elif target_person == "1st":
        res = re.sub(
            r"\b(?:himself/herself|herself|himself)\b",
            "myself",
            res,
            flags=re.IGNORECASE,
        )
        res = re.sub(
            r"\b(?:his/her|her)\s+(belt|clothes|shoes|hands|face|eyes|hair|arms|body)\b",
            r"my \1",
            res,
            flags=re.IGNORECASE,
        )
        res = re.sub(r"\bhim/her\b", "her", res, flags=re.IGNORECASE)
        res = re.sub(r"\bhis/her\b", "her", res, flags=re.IGNORECASE)
        res = re.sub(r"\bhe/she\b", "I", res, flags=re.IGNORECASE)
    elif target_person == "2nd":
        res = re.sub(
            r"\b(?:himself/herself|herself|himself)\b",
            "yourself",
            res,
            flags=re.IGNORECASE,
        )
        res = re.sub(
            r"\b(?:his/her|her)\s+(belt|clothes|shoes|hands|face|eyes|hair|arms|body)\b",
            r"your \1",
            res,
            flags=re.IGNORECASE,
        )
        res = re.sub(r"\bhim/her\b", "her", res, flags=re.IGNORECASE)
        res = re.sub(r"\bhis/her\b", "her", res, flags=re.IGNORECASE)
        res = re.sub(r"\bhe/she\b", "you", res, flags=re.IGNORECASE)
    return res


def _build_progressive_forms(
    subj_type: str,
    lemma: str,
    vbg: str,
    rest: str,
    form_name: str,
    parenthetical: str,
) -> str:
    vbz_tup = getInflection(lemma, "VBZ")
    vbz = vbz_tup[0] if vbz_tup else (lemma + "s")

    vbd_tup = getInflection(lemma, "VBD")
    vbd = vbd_tup[0] if vbd_tup else (lemma + "ed")

    subj_nom = "she" if subj_type == "she" else subj_type
    subj_obj = (
        "her"
        if subj_type == "she"
        else ("them" if subj_type == "they" else "it")
    )
    aux_pres = "are" if subj_type == "they" else "is"

    rest_3rd = clean_pronouns(rest, "3rd_she")
    rest_1st = clean_pronouns(rest, "1st")
    rest_2nd = clean_pronouns(rest, "2nd")

    space_3rd = f" {rest_3rd}" if rest_3rd else ""
    space_1st = f" {rest_1st}" if rest_1st else ""
    space_2nd = f" {rest_2nd}" if rest_2nd else ""

    if form_name == "present":
        return f"{subj_nom} {aux_pres} {vbg}{space_3rd}{parenthetical}"
    elif form_name == "imperfective":
        verb_form = lemma if subj_type == "they" else vbz
        return f"{subj_nom} {verb_form}{space_3rd}{parenthetical}"
    elif form_name == "perfective":
        return f"{subj_nom} {vbd}{space_3rd}{parenthetical}"
    elif form_name == "present_1sg":
        return f"I am {vbg}{space_1st}{parenthetical}"
    elif form_name == "imperative":
        return f"{lemma}{space_2nd}!{parenthetical}"
    elif form_name == "infinitive":
        return f"(for {subj_obj}) to {lemma}{space_3rd}{parenthetical}"
    return f"{subj_nom} {aux_pres} {vbg}{space_3rd}{parenthetical}"


def _build_stative_forms(
    subj_type: str,
    lemma: str,
    vbz: str,
    rest: str,
    form_name: str,
    parenthetical: str,
) -> str:
    vbd_tup = getInflection(lemma, "VBD")
    vbd = vbd_tup[0] if vbd_tup else (lemma + "ed")

    subj_nom = "she" if subj_type == "she" else subj_type
    subj_obj = (
        "her"
        if subj_type == "she"
        else ("them" if subj_type == "they" else "it")
    )

    rest_3rd = clean_pronouns(rest, "3rd_she")
    rest_1st = clean_pronouns(rest, "1st")
    rest_2nd = clean_pronouns(rest, "2nd")

    space_3rd = f" {rest_3rd}" if rest_3rd else ""
    space_1st = f" {rest_1st}" if rest_1st else ""
    space_2nd = f" {rest_2nd}" if rest_2nd else ""

    verb_3rd = lemma if subj_type == "they" else vbz

    if form_name == "present":
        return f"{subj_nom} {verb_3rd}{space_3rd}{parenthetical}"
    elif form_name == "imperfective":
        return f"{subj_nom} {verb_3rd}{space_3rd} (habitually){parenthetical}"
    elif form_name == "perfective":
        return f"{subj_nom} {vbd}{space_3rd}{parenthetical}"
    elif form_name == "present_1sg":
        return f"I {lemma}{space_1st}{parenthetical}"
    elif form_name == "imperative":
        return f"{lemma}{space_2nd}!{parenthetical}"
    elif form_name == "infinitive":
        return f"(for {subj_obj}) to {lemma}{space_3rd}{parenthetical}"
    return f"{subj_nom} {verb_3rd}{space_3rd}{parenthetical}"


def _build_copula_forms(
    subj_type: str,
    predicate: str,
    form_name: str,
    parenthetical: str,
) -> str:
    pred_3rd = clean_pronouns(predicate, "3rd_she")
    pred_1st = clean_pronouns(predicate, "1st")
    pred_2nd = clean_pronouns(predicate, "2nd")

    subj_nom = "she" if subj_type == "she" else subj_type
    subj_obj = (
        "her"
        if subj_type == "she"
        else (
            "them"
            if subj_type == "they"
            else ("there" if subj_type == "there" else "it")
        )
    )
    aux_pres = "are" if subj_type == "they" else "is"
    aux_past = "were" if subj_type == "they" else "was"

    if form_name == "present":
        return f"{subj_nom} {aux_pres} {pred_3rd}{parenthetical}"
    elif form_name == "imperfective":
        return f"{subj_nom} {aux_pres} {pred_3rd} (habitually){parenthetical}"
    elif form_name == "perfective":
        return f"{subj_nom} {aux_past} {pred_3rd}{parenthetical}"
    elif form_name == "present_1sg":
        if subj_type == "there":
            return f"there is {pred_1st}{parenthetical}"
        return f"I am {pred_1st}{parenthetical}"
    elif form_name == "imperative":
        if subj_type == "there":
            return f"let there be {pred_2nd}!{parenthetical}"
        return f"be {pred_2nd}!{parenthetical}"
    elif form_name == "infinitive":
        return f"(for {subj_obj}) to be {pred_3rd}{parenthetical}"
    return f"{subj_nom} {aux_pres} {pred_3rd}{parenthetical}"


def inflect_english_definition(definition: str, form_name: str) -> str:
    """
    Inflects an English CED verb definition into the specified Cherokee form.
    Forms:
    - 'present': Present tense / progressive (3rd person)
    - 'imperfective': Habitual / simple present
    - 'perfective': Completive / simple past
    - 'present_1sg': 1st person singular present
    - 'imperative': 2nd person command (ends with '!')
    - 'infinitive': '(for [subject_obj]) to [verb] ...'
    """
    d = normalize_definition(definition)

    parenthetical = ""
    paren_match = re.search(r"\s*(\([^)]+\))$", d)
    if paren_match:
        parenthetical = " " + paren_match.group(1).strip()
        d = d[: paren_match.start()].strip()

    # Pattern 1: Progressive "X is/are [VERB]ing ..." or "X's [VERB]ing ..."
    prog_match = re.match(
        r"^(he/she|it|they|he|she)(?:\s+(?:is|are)|'s)\s+([a-z]+ing)\b(.*)$",
        d,
        re.IGNORECASE,
    )
    if prog_match:
        s_raw, vbg, rest = prog_match.groups()
        s_lower = s_raw.lower()
        subj_type = (
            "it"
            if s_lower == "it"
            else ("they" if s_lower == "they" else "she")
        )

        lemmas = getLemma(vbg, "VERB")
        lemma = lemmas[0] if lemmas else vbg[:-3]
        if lemma == "be" and vbg == "being":
            lemma = "be"

        rest = rest.strip()
        return _build_progressive_forms(
            subj_type, lemma, vbg, rest, form_name, parenthetical
        )

    # Pattern 2: Simple present stative "X has / knows / lives / wants / hears / hates / likes / smells / understands / feels / loves / thinks / smells ..."
    simple_pres_match = re.match(
        r"^(he/she|it|they|he|she)\s+([a-z]+s|[a-z]+es|has)\b(.*)$",
        d,
        re.IGNORECASE,
    )
    if simple_pres_match:
        s_raw, vbz, rest = simple_pres_match.groups()
        s_lower = s_raw.lower()
        subj_type = (
            "it"
            if s_lower == "it"
            else ("they" if s_lower == "they" else "she")
        )

        lemmas = getLemma(vbz, "VERB")
        lemma = (
            lemmas[0]
            if lemmas
            else (vbz[:-2] if vbz.endswith("es") else vbz[:-1])
        )
        if vbz == "has":
            lemma = "have"

        rest = rest.strip()
        return _build_stative_forms(
            subj_type, lemma, vbz, rest, form_name, parenthetical
        )

    # Pattern 3: Copula + predicate "it's hot", "they are asleep", "there is dew", "he/she is in view"
    copula_match = re.match(
        r"^(he/she|it|they|he|she|there)(?:\s+(?:is|are)|'s)\s+(.+)$",
        d,
        re.IGNORECASE,
    )
    if copula_match:
        s_raw, predicate = copula_match.groups()
        s_lower = s_raw.lower()
        subj_type = (
            "it"
            if s_lower in ("it",)
            else (
                "they"
                if s_lower == "they"
                else ("there" if s_lower == "there" else "she")
            )
        )
        return _build_copula_forms(
            subj_type, predicate.strip(), form_name, parenthetical
        )

    return clean_pronouns(d, "3rd_she") + parenthetical
