import json
import os
import csv
from typing import List, Dict, Set, Tuple, Optional
from king_recreation.reconstruct_from_roots import ReconstructibleVerb


def analyze_post_root_morphemes(
    reconstructable_path: str, morphemes_path: str, output_path: str
):
    if not os.path.exists(reconstructable_path):
        print(f"Error: Input file {reconstructable_path} not found.")
        return

    if not os.path.exists(morphemes_path):
        print(f"Error: Morphemes file {morphemes_path} not found.")
        return

    # Load existing approvals
    existing_approvals: Dict[Tuple[str, str, str, str], str] = {}
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Key: (from_h, from_class, to_h)
                key = (
                    row.get("from_h_grade", ""),
                    row.get("from_class", ""),
                    row.get("to_h_grade", ""),
                )
                existing_approvals[key] = row.get("user_approved", "")

    # Load Verbs
    with open(reconstructable_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    verbs: List[ReconstructibleVerb] = [
        ReconstructibleVerb.from_dict(item) for item in data
    ]

    # Group verbs by (h_grade, g_grade, class)
    # Using (h, g, class) as unique identifier for a group of verbs (same morphology)
    root_groups: Dict[Tuple[str, str, str], Dict] = {}

    # Also index groups by (h_grade) for loose matching if needed,
    # but strictly we usually match h_grade and g_grade (stripped).
    # Since the morpheme removal might affect g-grade unpredictably (or we ignore it),
    # we will focus on h-grade modification as the primary key.

    # Base lookup: h_grade -> list of groups
    base_lookup: Dict[str, List[Dict]] = {}

    for verb in verbs:
        key = (verb.h_grade_root, verb.glottal_grade_root or "", verb.class_name)
        if key not in root_groups:
            group = {
                "h_grade": verb.h_grade_root,
                "g_grade": verb.glottal_grade_root or "",
                "class": verb.class_name,
                "corpus_ids": [],
            }
            root_groups[key] = group

            h = verb.h_grade_root
            if h not in base_lookup:
                base_lookup[h] = []
            base_lookup[h].append(group)

        root_groups[key]["corpus_ids"].append(str(verb.corpus_id))

    # Load Morphemes
    morphemes = []
    with open(morphemes_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            morphemes.append(row)

    rows = []

    # Iterate through all verb groups
    for key, group in root_groups.items():
        h_root = group["h_grade"]
        cls = group["class"]

        # Check against all morpheme patterns
        for morpheme in morphemes:
            suffix = morpheme["form"]
            target_classes = morpheme["classes"].split(
                ";"
            )  # semi-colon separated just in case
            target_classes = [c.strip() for c in target_classes]

            # check class match
            if cls not in target_classes:
                continue

            # check suffix match
            if h_root.endswith(suffix):
                # Candidate found!
                # Attempt to find base
                base_h = h_root[: -len(suffix)]

                # We need to find if this base exists in the corpus
                # The user requirement: "check if roots have 1. the right ending and 2. end with the sequence given by the form column"
                # (I interpreted 'ending' as class-based ending logic, but here it seems we are just stripping the string suffix)

                candidate_bases = base_lookup.get(base_h, [])

                # Filter candidate bases?
                # For now, just link to all matches or flag if none.

                if not candidate_bases:
                    # No base found - Flag it
                    # Key for no match: (from_h, from_class, to_h_candidate)
                    row_data = {
                        "user_approved": existing_approvals.get(
                            (h_root, cls, base_h), ""
                        ),
                        "morpheme_name": morpheme["name"],
                        "morpheme_subcase": morpheme.get("subcase", ""),
                        "from_h_grade": h_root,
                        "from_g_grade": group["g_grade"],
                        "from_class": cls,
                        "from_corpus_ids": ";".join(group["corpus_ids"]),
                        "to_h_grade": base_h,  # The theoretical base
                        "to_g_grade": "",
                    }
                    rows.append(row_data)
                else:
                    # Collect unique target roots (h_grade, g_grade)
                    # We might have multiple classes for the same root, but we only care about the root itself now.
                    target_roots = set()
                    for base in candidate_bases:
                        target_roots.add((base["h_grade"], base["g_grade"]))

                    for t_h, t_g in target_roots:
                        # Prevent self-linking if it's strictly the same root forms
                        if t_h == h_root and t_g == group["g_grade"]:
                            continue

                        approval_key = (h_root, cls, t_h)

                        row_data = {
                            "user_approved": existing_approvals.get(approval_key, ""),
                            "morpheme_name": morpheme["name"],
                            "morpheme_subcase": morpheme.get("subcase", ""),
                            "from_h_grade": h_root,
                            "from_g_grade": group["g_grade"],
                            "from_class": cls,
                            "from_corpus_ids": ";".join(group["corpus_ids"]),
                            "to_h_grade": t_h,
                            "to_g_grade": t_g,
                        }
                        rows.append(row_data)

    # Sort rows
    rows.sort(key=lambda x: (x["from_h_grade"], x["from_class"], x["to_h_grade"]))

    # Output
    fieldnames = [
        "user_approved",
        "morpheme_name",
        "morpheme_subcase",
        "from_h_grade",
        "from_g_grade",
        "from_class",
        "from_corpus_ids",
        "to_h_grade",  # The base root
        "to_g_grade",
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Analyzed post-root morphemes. Found {len(rows)} connections (including potential orphans)."
    )
    print(f"Results written to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze post-root morphemes.")
    parser.add_argument(
        "--verbs",
        default="artifacts/data/reconstructable_verbs.json",
        help="Path to verbs JSON",
    )
    parser.add_argument(
        "--morphemes",
        default="data/post_root_morphemes.csv",
        help="Path to morphemes CSV",
    )
    parser.add_argument(
        "--output",
        default="artifacts/data/post_root_connections.csv",
        help="Output path",
    )
    args = parser.parse_args()

    analyze_post_root_morphemes(args.verbs, args.morphemes, args.output)
