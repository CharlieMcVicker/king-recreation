import io
import json
import re
import unicodedata
from collections import defaultdict
from csv import DictReader
from dataclasses import dataclass
from enum import Enum
from typing import List, Union

from king_recreation.paths import (
    cherokee_nation_dictionary_path,
    class_ending_profiles_csv_path,
    corpus_to_cnd_path,
    ending_tone_analysis_csv_path,
    ending_tone_analysis_json_path,
    reconstructable_verbs_path,
)
from king_recreation.phonology_data import VOWEL_SET
from king_recreation.preprocess_ced import respell_consonants
from king_recreation.reconstruct_from_roots import (
    ReconstructibleVerb,
    drop_dropped_phones,
)


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
    s = "4"

    @staticmethod
    def from_mark_and_length(mark: str, long: bool):
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


def get_tone_sequence_for_form(
    verb, form_name, cnd_corpus, corpus_id_to_entries
) -> List[Vowel]:
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


def apply_tone_to_segmentation(segmented: str, tone_seq: List[Vowel]) -> str:
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


def main(interactive=False):

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
        # "No." seems to be the grouping ID, but "Entry No." is unique per row.
        # corpus_to_cnd maps to "Entry No."
        cnd_corpus = {r.get("Entry No.", "").strip(): r for r in reader}

    forms_to_check = [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]

    class_ending_tone_verbs = defaultdict(lambda: defaultdict(lambda: defaultdict(set)))
    class_surface_to_verbs = defaultdict(lambda: defaultdict(set))
    # Profile: (class, present, imperfective, perfective, imperative, infinitive) -> set(corpus_id)
    class_profile_to_verbs = defaultdict(set)

    for verb in reconstructable_verbs:
        cls = verb.class_name
        profile = []

        main_profile_forms = [
            "present",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]

        # We also want to populate the individual mappings as before
        for form in forms_to_check:
            segmented = verb.segmented_forms.get(form, "")
            surface = ""
            if segmented:
                tone_seq = get_tone_sequence_for_form(
                    verb, form, cnd_corpus, corpus_id_to_entries
                )
                if tone_seq:
                    combined = apply_tone_to_segmentation(segmented, tone_seq)
                    if "-" in combined:
                        final_combined_segment = combined.split("-")[-1]
                        surface = final_combined_segment

                        tones = re.findall(r"\d+", final_combined_segment)
                        base_ending = re.sub(r"\d+", "", final_combined_segment)
                        if tones:
                            class_ending_tone_verbs[cls][base_ending][str(tones)].add(
                                verb.corpus_id
                            )
                            class_surface_to_verbs[cls][final_combined_segment].add(
                                verb.corpus_id
                            )

            if form in main_profile_forms:
                profile.append(surface)

        profile_key = (cls,) + tuple(profile)
        class_profile_to_verbs[profile_key].add(verb.corpus_id)

    # Merge profiles with null forms
    while True:
        to_merge = None
        current_keys = list(class_profile_to_verbs.keys())
        for p in current_keys:
            if "" not in p[1:]:  # Skip if no null forms
                continue

            # Find all profiles q that "contain" p (same class, p's non-empty match q's)
            matches = []
            for q in current_keys:
                if p == q:
                    continue
                # q must match p in all non-empty positions
                if p[0] != q[0]:
                    continue

                is_match = True
                has_more_info = False
                for idx in range(1, len(p)):
                    if p[idx] != "":
                        if p[idx] != q[idx]:
                            is_match = False
                            break
                    elif q[idx] != "":
                        has_more_info = True

                if is_match and has_more_info:
                    matches.append(q)

            if len(matches) == 1:
                to_merge = (p, matches[0])
                break

        if not to_merge:
            break

        p, q = to_merge
        # Merge p's verbs into q
        verbs_to_move = class_profile_to_verbs[p]
        class_profile_to_verbs[q].update(verbs_to_move)

        # Also update individual surface counts for inferred forms
        # (This ensures ending_tone_analysis.csv remains consistent with profiles)
        for idx in range(1, len(p)):
            if p[idx] == "" and q[idx] != "":
                inferred_surface = q[idx]
                class_surface_to_verbs[p[0]][inferred_surface].update(verbs_to_move)

                # Update class_ending_tone_verbs as well
                tones = re.findall(r"\d+", inferred_surface)
                base_ending = re.sub(r"\d+", "", inferred_surface)
                if tones:
                    class_ending_tone_verbs[p[0]][base_ending][str(tones)].update(
                        verbs_to_move
                    )

        del class_profile_to_verbs[p]

    # Save to artifacts
    import csv
    import os

    # JSON Output
    artifact_output = {}
    for cls in sorted(class_ending_tone_verbs.keys()):
        cls_data = {}
        for ending in sorted(class_ending_tone_verbs[cls].keys()):
            cls_data[ending] = sorted(list(class_ending_tone_verbs[cls][ending].keys()))
        artifact_output[cls] = cls_data

    os.makedirs(os.path.dirname(ending_tone_analysis_json_path), exist_ok=True)
    with open(ending_tone_analysis_json_path, "w") as f:
        json.dump(artifact_output, f, indent=4, sort_keys=True)

    # CSV Output
    # We want Class, Surface Form, Count
    # We can also include Base Ending and Tones for clarity
    csv_rows = []
    for cls in sorted(class_surface_to_verbs.keys()):
        for surface_form in sorted(class_surface_to_verbs[cls].keys()):
            count = len(class_surface_to_verbs[cls][surface_form])
            # Decompose for CSV columns
            tones = re.findall(r"\d+", surface_form)
            base_ending = re.sub(r"\d+", "", surface_form)

            csv_rows.append(
                {
                    "Class": cls,
                    "Surface Form": surface_form,
                    "Base Ending": base_ending,
                    "Tones": "-".join(tones),
                    "Count": count,
                }
            )

    with open(ending_tone_analysis_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["Class", "Surface Form", "Base Ending", "Tones", "Count"]
        )
        writer.writeheader()
        writer.writerows(csv_rows)

    # Class Ending Profiles Output
    profile_rows = []
    for (cls, pres, imperf, perf, impv, inf), verbs in class_profile_to_verbs.items():
        profile_rows.append(
            {
                "class": cls,
                "present": pres,
                "imperfective": imperf,
                "perfective": perf,
                "immediate": impv,
                "infinitive": inf,
                "count": len(verbs),
            }
        )

    # Sort by class then by forms
    profile_rows.sort(
        key=lambda x: (
            x["class"],
            x["present"],
            x["imperfective"],
            x["perfective"],
            x["immediate"],
            x["infinitive"],
        )
    )

    with open(class_ending_profiles_csv_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class",
                "present",
                "imperfective",
                "perfective",
                "immediate",
                "infinitive",
                "count",
            ],
        )
        writer.writeheader()
        writer.writerows(profile_rows)

    print(
        f"\nEnding Tone Analysis saved to:\n  JSON: {ending_tone_analysis_json_path}\n  CSV (Individual): {ending_tone_analysis_csv_path}\n  CSV (Profiles): {class_ending_profiles_csv_path}"
    )

    print("\nEnding Tone Analysis Summary by Class:")
    for cls in sorted(class_ending_tone_verbs.keys()):
        print(f"\nClass: {cls}")
        print(f"  {'Ending':<15} | {'Unique Tone Sequences'}")
        print("  " + "-" * 60)
        for ending in sorted(class_ending_tone_verbs[cls].keys()):
            sequences = sorted(list(class_ending_tone_verbs[cls][ending].keys()))
            print(f"  {ending:<15} | {', '.join(sequences)}")

    print("\n" + "=" * 60 + "\n")

    if not interactive:
        return

    for verb in reconstructable_verbs:
        print(f"\nVerb: {verb.definition} ({verb.h_grade_root})")
        print(
            f"{'Form':<15} | {'Segmented':<30} | {'Combined':<30} | {'Reference':<30}"
        )
        print("-" * 110)

        for form in forms_to_check:
            segmented = verb.segmented_forms.get(form, "")
            if not segmented:
                continue

            tone_seq = get_tone_sequence_for_form(
                verb, form, cnd_corpus, corpus_id_to_entries
            )

            combined = ""
            ref_str = ""

            if tone_seq:
                combined = apply_tone_to_segmentation(segmented, tone_seq)
                ref_str = "".join([str(t) for t in tone_seq])
            else:
                combined = "No Ref Tone"

            print(f"{form:<15} | {segmented:<30} | {combined:<30} | {ref_str:<30}")

        input("\nPress Enter for next verb...")


if __name__ == "__main__":
    main(interactive=True)
