"""
Fuzzy matching and verb priority ranking based on Kirk's verb list (kirkcsv.csv).

Ranks verbs within classes so that top frequency verbs (first5, first25, first100,
first200, etc.) appear first in study sequence after the class mascot.
"""

from __future__ import annotations

import csv
import os
import re
from typing import Any

from rapidfuzz import fuzz

from dictionary_pipeline.dictionary_forms import DictionaryVerb
from dictionary_pipeline.orthography import unrespell_consonants
from morphology.reconstruction import drop_dropped_phones

DEFAULT_KIRK_CSV = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "kirkcsv.csv")
)


def normalize_english(s: str) -> str:
    """
    Normalizes English verb definitions by removing subject pronouns,
    auxiliary verbs, numbers, and common stop words.
    """
    if not s:
        return ""
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = re.sub(r"\b\d+\.\s*", "", s)
    pronouns = [
        r"\bhe/she is\b",
        r"\bhe is\b",
        r"\bshe is\b",
        r"\bit is\b",
        r"\bit's\b",
        r"\bits\b",
        r"\bhe's\b",
        r"\bshe's\b",
        r"\bthey are\b",
        r"\bthey're\b",
        r"\bwe are\b",
        r"\bwe're\b",
        r"\bi am\b",
        r"\bi'm\b",
        r"\byou are\b",
        r"\byou're\b",
        r"\bhe\b",
        r"\bshe\b",
        r"\bit\b",
        r"\bthey\b",
        r"\bwe\b",
        r"\bi\b",
        r"\byou\b",
        r"\bhim/her/it\b",
        r"\bhim/her\b",
        r"\bhim\b",
        r"\bher\b",
        r"\bfor him/her to\b",
        r"\bfor her to\b",
        r"\bfor him to\b",
        r"\bfor me to\b",
        r"\bfor you to\b",
        r"\bfor them to\b",
        r"\bfor us to\b",
        r"\bto\b",
    ]
    for p in pronouns:
        s = re.sub(p, " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    tokens = [
        t
        for t in s.split()
        if t
        not in {
            "a",
            "an",
            "the",
            "and",
            "or",
            "of",
            "in",
            "on",
            "at",
            "so",
            "just",
            "habitually",
        }
    ]
    return " ".join(tokens)


def normalize_cherokee(s: str) -> str:
    """
    Normalizes Cherokee phonetic/segmented forms into comparable clean orthography.
    """
    if not s:
        return ""
    s = drop_dropped_phones(s)
    s = unrespell_consonants(s)
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = re.sub(r"[0-9\?\.\,\;\:\'\"\-\(\)\[\]\/\*\!\`\s\^]", "", s)
    s = s.replace("qu", "gw").replace("tl", "dl")
    return s


def load_kirk_verbs(csv_path: str = DEFAULT_KIRK_CSV) -> dict[int, dict[str, Any]]:
    """
    Loads kirkcsv.csv and groups by unique Verb Number.
    Assigns importance tiers:
        Tier 1: 'first5'
        Tier 2: 'first25'
        Tier 3: 'first100'
        Tier 4: 'first200'
        Tier 5: other verbs in Kirk list
    """
    if not os.path.exists(csv_path):
        return {}

    kirk_verbs: dict[int, dict[str, Any]] = {}
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            vn_str = r.get("Verb Number", "").strip()
            if not vn_str:
                continue
            vn = int(vn_str)
            if vn not in kirk_verbs:
                tags = set(r.get("tags", "").split())
                tier = 5
                if "first5" in tags:
                    tier = 1
                elif "first25" in tags:
                    tier = 2
                elif "first100" in tags:
                    tier = 3
                elif "first200" in tags:
                    tier = 4

                k_cher = normalize_cherokee(r.get("Kirk Verb (Cherokee)", ""))
                ced_cher = normalize_cherokee(r.get("CED (Cherokee)", ""))
                k_eng = normalize_english(r.get("Kirk Verb (English)", ""))
                ced_eng = normalize_english(r.get("CED (English)", ""))

                kirk_verbs[vn] = {
                    "vn": vn,
                    "tier": tier,
                    "tags": tags,
                    "raw_cher": r.get("Kirk Verb (Cherokee)", ""),
                    "raw_eng": r.get("Kirk Verb (English)", ""),
                    "cher_list": [c for c in (k_cher, ced_cher) if c],
                    "eng_list": [e for e in (k_eng, ced_eng) if e],
                }

    return kirk_verbs


def compute_verb_priority(
    verbs: list[DictionaryVerb],
    kirk_csv_path: str = DEFAULT_KIRK_CSV,
) -> dict[int, tuple[int, int, float]]:
    """
    Fuzzy-matches a collection of DictionaryVerbs against Kirk verbs.
    Returns a mapping from id(verb) -> (tier, kirk_verb_number, -match_score).
    Unmatched verbs receive tier 6 and verb number 9999.
    """
    kirk_verbs = load_kirk_verbs(kirk_csv_path)
    if not kirk_verbs:
        return {id(v): (6, 9999, 0.0) for v in verbs}

    priority_map: dict[int, tuple[int, int, float]] = {}

    for v in verbs:
        v_eng = normalize_english(v.definition)
        pres_seg = v.segmented_forms.get("present", "")
        pres_cher = (
            normalize_cherokee(pres_seg)
            if pres_seg and pres_seg != "---"
            else ""
        )
        root_cher = normalize_cherokee(v.morphology.h_grade_root)
        v_cher_list = [c for c in (pres_cher, root_cher) if c]

        best_score = 0.0
        best_match: dict[str, Any] | None = None

        for vn, kv in kirk_verbs.items():
            # English similarity
            eng_score = 0.0
            for ke in kv["eng_list"]:
                if v_eng == ke:
                    eng_score = 100.0
                    break
                tsr = fuzz.token_set_ratio(v_eng, ke)
                if tsr > eng_score:
                    eng_score = tsr

            # Cherokee similarity
            cher_score = 0.0
            for vc in v_cher_list:
                for kc in kv["cher_list"]:
                    if vc == kc:
                        cher_score = 100.0
                        break
                    r = fuzz.ratio(vc, kc)
                    if r > cher_score:
                        cher_score = r

            # Hybrid scoring logic requiring both semantic and phonological confirmation
            if eng_score >= 80 and cher_score >= 65:
                score = eng_score * 0.5 + cher_score * 0.5 + 20.0
            elif eng_score >= 95 and cher_score >= 50:
                score = eng_score * 0.6 + cher_score * 0.4 + 10.0
            elif cher_score >= 90 and eng_score >= 50:
                score = cher_score * 0.6 + eng_score * 0.4 + 10.0
            else:
                score = 0.0

            if score > best_score:
                best_score = score
                best_match = kv

        if best_match and best_score >= 75.0:
            priority_map[id(v)] = (
                best_match["tier"],
                best_match["vn"],
                -best_score,
            )
        else:
            priority_map[id(v)] = (6, 9999, 0.0)

    return priority_map
