import re
from collections import defaultdict

from king_recreation.phases.check_tone_consistency.artifacts import (
    load_cnd_corpus,
    save_class_ending_profiles,
    save_tone_analysis_csv,
    save_tone_analysis_json,
)
from king_recreation.phases.preprocess_ced.artifacts import (
    load_mapping as load_corpus_mapping,
)
from king_recreation.phases.select_canonical_derivations.artifacts import (
    load_reconstructable_verbs as load_raw_reconstructable_verbs,
)
from king_recreation.tone.utils import (
    apply_tone_to_segmentation,
    get_tone_sequence_for_form,
)


def check_tone_consistency(interactive: bool = False) -> None:
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

    reconstructable_verbs = load_raw_reconstructable_verbs()
    if not reconstructable_verbs:
        print("Required inputs missing.")
        return

    mapping = load_corpus_mapping()
    corpus_id_to_entries = {int(r["corpus_id"]): r for r in mapping}
    if not corpus_id_to_entries:
        print("Corpus to CND mapping missing.")
        return

    cnd_corpus = load_cnd_corpus()
    if not cnd_corpus:
        print("CND corpus missing.")
        return

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
        cls = verb.morphology.class_name
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

    save_tone_analysis_json(artifact_output)

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

    save_tone_analysis_csv(
        csv_rows, ["Class", "Surface Form", "Base Ending", "Tones", "Count"]
    )

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

    save_class_ending_profiles(
        profile_rows,
        [
            "class",
            "present",
            "imperfective",
            "perfective",
            "immediate",
            "infinitive",
            "count",
        ],
    )

    print(f"\nEnding Tone Analysis saved.")

    # print("\nEnding Tone Analysis Summary by Class:")
    # for cls in sorted(class_ending_tone_verbs.keys()):
    #     print(f"\nClass: {cls}")
    #     print(f"  {'Ending':<15} | {'Unique Tone Sequences'}")
    #     print("  " + "-" * 60)
    #     for ending in sorted(class_ending_tone_verbs[cls].keys()):
    #         sequences = sorted(list(class_ending_tone_verbs[cls][ending].keys()))
    #         print(f"  {ending:<15} | {', '.join(sequences)}")

    # print("\n" + "=" * 60 + "\n")

    if not interactive:
        return

    for verb in reconstructable_verbs:
        print(f"\nVerb: {verb.definition} ({verb.morphology.h_grade_root})")
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
