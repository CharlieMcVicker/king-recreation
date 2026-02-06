import io
import json
import unicodedata
from csv import DictReader
from dataclasses import dataclass
from enum import Enum
from typing import List, Union

from king_recreation.paths import (
    cherokee_nation_dictionary_path,
    corpus_to_cnd_path,
    reconstructable_verbs_path,
)
from king_recreation.phonology_data import VOWEL_SET
from king_recreation.preprocess_ced import respell_consonants
from king_recreation.reconstruct_from_roots import ReconstructibleVerb


@dataclass
class Consonant:
    value: str
    idx_start: int
    idx_end: int

    def __str__(self):
        return self.value


class VowelTone(Enum):
    l = "2"
    ll = "22"
    lf = "21"
    lh = "23"
    hl = "32"
    h = "3"
    hh = "33"
    sh = "44"

    @staticmethod
    def from_mark_and_length(mark: str, long: bool):
        if mark == ACUTE:
            if long:
                return VowelTone.hh
            else:
                return VowelTone.h
        elif mark == GRAVE:
            if long:
                return VowelTone.lf
            else:
                raise Exception("Short lowfall is bunk")
        elif mark == D_ACUTE:
            if long:
                return VowelTone.sh
            else:
                raise Exception("Short superhigh is bunk")
        elif mark == CIRCUM:
            if long:
                return VowelTone.hl
            else:
                raise Exception("Short falling is bunk")
        elif mark == CARON:
            if long:
                return VowelTone.lh
            else:
                raise Exception("Short rising is bunk")
        else:
            if long:
                return VowelTone.ll
            else:
                return VowelTone.l

    def __str__(self):
        return self.value


ACUTE = "\u0301"  # acute
GRAVE = "\u0300"  # grave
D_ACUTE = "\u030b"  # double acute
CIRCUM = "\u0302"  # circumflex
CARON = "\u030c"  # upside down circumflex
TONE_MARKS = {ACUTE, GRAVE, D_ACUTE, CIRCUM, CARON}


@dataclass
class Vowel:
    quality: str
    tone: VowelTone

    idx_start: int
    idx_end: int

    def __str__(self):
        return self.quality + str(self.tone)


def split_diacritics(raw: str) -> str:
    return unicodedata.normalize("NFD", raw)


def safe_get(l, idx):
    if idx < len(l):
        return l[idx]
    else:
        return None


def read_tone_sequence(raw: str) -> List[Union[Vowel, Consonant]]:
    raw = list(c for c in raw)
    seq = []
    idx = 0
    while idx < len(raw):
        c = raw[idx]
        if c not in VOWEL_SET:
            seq.append(Consonant(value=c, idx_start=idx, idx_end=idx))
            idx += 1
        else:
            quality = c
            idx_start = idx
            idx += 1
            if safe_get(raw, idx) in TONE_MARKS:
                tone_mark = raw[idx]
                idx += 1
            else:
                tone_mark = None

            if safe_get(raw, idx) == ":":
                long = True
                idx += 1
            else:
                long = False

            seq.append(
                Vowel(
                    quality,
                    VowelTone.from_mark_and_length(tone_mark, long),
                    idx_start=idx_start,
                    idx_end=idx - 1,
                )
            )
    return seq


def main():

    with open(reconstructable_verbs_path, "r") as f:
        reconstructable_verbs_raw = json.load(f)
    reconstructable_verbs = [
        ReconstructibleVerb.from_dict(v) for v in reconstructable_verbs_raw
    ]

    with open(corpus_to_cnd_path, "r") as f:
        reader = DictReader(f)
        corpus_id_to_entries = {int(r["corpus_id"]): r for r in reader}

    with open(cherokee_nation_dictionary_path, "r") as f:

        content = f.read()
        if content.startswith("\ufeff"):
            content = content[1:]

        reader = DictReader(io.StringIO(content))
        cnd_corpus = {r.get("Entry No.", "").strip(): r for r in reader}

    for verb in reconstructable_verbs:
        tone_raw = split_diacritics(
            respell_consonants(
                cnd_corpus[corpus_id_to_entries[verb.corpus_id]["present"]][
                    "Tone and length 2"
                ]
            )
        )
        prac = respell_consonants(
            cnd_corpus[corpus_id_to_entries[verb.corpus_id]["present"]]["Practical"]
        )
        tokens = read_tone_sequence(tone_raw)

        start = prac.find(verb.h_grade_root)
        if start == -1:
            # print(prac, "does not contain h_grade root", verb.h_grade_root)
            continue

        tok_sub = tokens[start : start + len(verb.h_grade_root)]
        prac_sub = prac[start : start + len(verb.h_grade_root)]
        tone_raw_sub = (
            tone_raw[tok_sub[0].idx_start : tok_sub[-1].idx_end] if len(tok_sub) else []
        )

        print(prac_sub, tone_raw_sub, "".join([str(tok) for tok in tok_sub]))

        # print(s2)
        # for t in toks:
        #     print(t)
        # input()


if __name__ == "__main__":
    main()
