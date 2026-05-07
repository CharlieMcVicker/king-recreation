import unicodedata
from dataclasses import dataclass
from enum import Enum

from king_recreation.phases.preprocess_ced import respell_consonants
from king_recreation.phonology_data import VOWEL_SET
from king_recreation.reconstruction import drop_dropped_phones


@dataclass
class Consonant:
    value: str

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
    s = "4"

    @staticmethod
    def from_mark_and_length(mark: str | None, long: bool) -> "VowelTone":
        mapping = {
            ACUTE: (VowelTone.h, VowelTone.hh),
            GRAVE: (VowelTone.l, VowelTone.lf),
            D_ACUTE: (VowelTone.s, VowelTone.sh),
            CIRCUM: (VowelTone.h, VowelTone.hl),
            CARON: (VowelTone.l, VowelTone.lh),
            None: (VowelTone.l, VowelTone.ll),
        }
        short, long_tone = mapping.get(mark, (VowelTone.l, VowelTone.ll))
        return long_tone if long else short

    def __str__(self):
        return self.value


TONE_VALUE_TO_ENUM = {v.value: v for v in VowelTone}


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

    def __str__(self):
        return self.quality + str(self.tone)


def split_diacritics(raw: str) -> str:
    return unicodedata.normalize("NFD", raw)


def safe_get(l: list, idx: int):
    if idx < len(l):
        return l[idx]
    else:
        return None


def read_tone_sequence(raw_str: str) -> list[Vowel | Consonant]:
    raw = list(c for c in raw_str)
    seq = []
    idx = 0
    while idx < len(raw):
        c = raw[idx]
        if c not in VOWEL_SET:
            seq.append(Consonant(value=c))
            idx += 1
        else:
            quality = c
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
                )
            )
    return seq


def get_tone_sequence_for_form(
    verb, form_name: str, cnd_corpus: dict, corpus_id_to_entries: dict
) -> list[Vowel | Consonant]:
    entry_map = corpus_id_to_entries.get(verb.corpus_id)
    if not entry_map:
        return []

    cnd_ref_id = entry_map.get(form_name)
    if not cnd_ref_id:
        return []

    cnd_entry = cnd_corpus.get(cnd_ref_id)
    if not cnd_entry:
        return []

    # Tone and length 2 seems to be the standard field for the entry's main form
    # matching the row in CND.
    raw_tone = cnd_entry.get("Tone and length 2", "")
    if not raw_tone:
        if raw_tone == "":
            return []
        # Fallback? No, just no tone.

    # Clean up/Respell
    tone_raw = split_diacritics(respell_consonants(raw_tone))
    return read_tone_sequence(tone_raw)


def apply_tone_to_segmentation(
    segmented: str, tone_seq: list[Vowel | Consonant]
) -> str:
    # Preprocess segmented form to remove dropped phones (markers like >a, i@, v*)
    segmented = drop_dropped_phones(segmented)

    # Attempt to align vowels in segmented form with tones in tone_seq
    output = []
    tone_idx = 0

    # We ignore non-vowels in tone_seq for count matching,
    # but read_tone_sequence returns Vowel and Consonant objects.
    # We should filter tone_seq to just vowels for alignment?
    # Or align strictly? The segmentation often has more/different consonants.
    # Let's align vowels.

    vowel_tones = [t for t in tone_seq if isinstance(t, Vowel)]

    i = 0
    while i < len(segmented):
        char = segmented[i]
        if char in VOWEL_SET:
            if tone_idx < len(vowel_tones):
                tone_obj = vowel_tones[tone_idx]
                tone_val = tone_obj.tone.value
                output.append(char + tone_val)
                tone_idx += 1
            else:
                output.append(char + "?")
        else:
            output.append(char)
        i += 1

    return "".join(output)


def strip_morpheme_boundaries(s: str) -> str:
    return s.replace("-", "")
