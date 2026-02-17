import csv
import io
import json
import os
import re
from collections import defaultdict
from csv import DictReader

from king_recreation.paths import (
    CHEROKEE_NATION_DICTIONARY_PATH,
    CLASS_ENDING_PROFILES_CSV_PATH,
    CORPUS_TO_CND_PATH,
    ENDING_TONE_ANALYSIS_CSV_PATH,
    ENDING_TONE_ANALYSIS_JSON_PATH,
    RECONSTRUCTABLE_VERBS_PATH,
)
from king_recreation.reconstruction import ReconstructableVerb
from king_recreation.tone.utils import (
    apply_tone_to_segmentation,
    get_tone_sequence_for_form,
)


def check_tone_consistency(interactive=False):
    """
    Check tone consistency for reconstructed verbs against the Cherokee Nation Dictionary.

    Matches segmented forms with CND entries to verify tone patterns and generate
    ending tone profiles for each verb class.

    Inputs:
    * RECONSTRUCTABLE_VERBS_PATH: List of reconstructed verbs with segmentation.
    * CORPUS_TO_CND_PATH: Mapping from corpus IDs to CND entry numbers.
    * CHEROKEE_NATION_DICTIONARY_PATH: The CND source file.

    Outputs:
    * ENDING_TONE_ANALYSIS_JSON_PATH: Detailed tone analysis by class and ending.
    * ENDING_TONE_ANALYSIS_CSV_PATH: Flat CSV of tone patterns by class and surface form.
    * CLASS_ENDING_PROFILES_CSV_PATH: Summary of tone profiles across aspect forms for each class.
    """

    if not os.path.exists(RECONSTRUCTABLE_VERBS_PATH):
        print(f"Error: {RECONSTRUCTABLE_VERBS_PATH} not found.")
        return

    with open(RECONSTRUCTABLE_VERBS_PATH, "r") as f:
        reconstructable_verbs_raw = json.load(f)
    reconstructable_verbs = [
        ReconstructableVerb.from_dict(v) for v in reconstructable_verbs_raw
    ]

    if not os.path.exists(CORPUS_TO_CND_PATH):
        print(f"Error: {CORPUS_TO_CND_PATH} not found. Tone check skipped.")
        return

    with open(CORPUS_TO_CND_PATH, "r") as f:
        reader = DictReader(f)
        corpus_id_to_entries = {int(r["corpus_id"]): r for r in reader}

    if not os.path.exists(CHEROKEE_NATION_DICTIONARY_PATH):
        print(
            f"Error: {CHEROKEE_NATION_DICTIONARY_PATH} not found. Tone check skipped."
        )
        return

    with open(CHEROKEE_NATION_DICTIONARY_PATH, "r") as f:
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
    # JSON Output
    artifact_output = {}
    for cls in sorted(class_ending_tone_verbs.keys()):
        cls_data = {}
        for ending in sorted(class_ending_tone_verbs[cls].keys()):
            cls_data[ending] = sorted(list(class_ending_tone_verbs[cls][ending].keys()))
        artifact_output[cls] = cls_data

    os.makedirs(os.path.dirname(ENDING_TONE_ANALYSIS_JSON_PATH), exist_ok=True)
    with open(ENDING_TONE_ANALYSIS_JSON_PATH, "w") as f:
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

    with open(ENDING_TONE_ANALYSIS_CSV_PATH, "w", newline="") as f:
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

    with open(CLASS_ENDING_PROFILES_CSV_PATH, "w", newline="") as f:
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
        f"\nEnding Tone Analysis saved to:\n  JSON: {ENDING_TONE_ANALYSIS_JSON_PATH}\n  CSV (Individual): {ENDING_TONE_ANALYSIS_CSV_PATH}\n  CSV (Profiles): {CLASS_ENDING_PROFILES_CSV_PATH}"
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
    check_tone_consistency(interactive=True)
