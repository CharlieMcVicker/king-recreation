import csv
import os
from typing import Dict, List, Optional, Set, Tuple

from king_recreation.utils import (
    group_verbs_by_root,
    load_existing_approvals,
    load_verbs,
    save_csv_artifact,
)


def analyze_post_root_morphemes(
    reconstructable_path: str,
    morphemes_path: str,
    output_path: str,
    verbs: List = None,
    root_groups: Dict = None,
):
    if verbs is None or root_groups is None:
        if not os.path.exists(reconstructable_path):
            print(f"Error: Input file {reconstructable_path} not found.")
            return
        verbs = load_verbs(reconstructable_path)
        root_groups = group_verbs_by_root(verbs)

    if not os.path.exists(morphemes_path):
        print(f"Error: Morphemes file {morphemes_path} not found.")
        return

    # Load existing approvals
    approval_key_fields = ["from_h_grade", "from_class", "to_h_grade"]
    existing_approvals = load_existing_approvals(output_path, approval_key_fields)

    # Base lookup: h_grade -> list of groups
    base_lookup: Dict[str, List[Dict]] = {}
    for group in root_groups.values():
        h = group["h_grade"]
        if h not in base_lookup:
            base_lookup[h] = []
        base_lookup[h].append(group)

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
            target_classes = [c.strip() for c in morpheme["classes"].split(";")]

            # check class match
            if cls not in target_classes:
                continue

            # check suffix match
            if h_root.endswith(suffix):
                # Candidate found!
                # Attempt to find base
                base_h = h_root[: -len(suffix)]
                candidate_bases = base_lookup.get(base_h, [])

                if not candidate_bases:
                    # No base found - Flag it
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
                        "to_h_grade": base_h,
                        "to_g_grade": "",
                    }
                    rows.append(row_data)
                else:
                    # Collect unique target roots (h_grade, g_grade)
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
        "to_h_grade",
        "to_g_grade",
    ]
    save_csv_artifact(output_path, fieldnames, rows)

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
        default="artifacts/connections/post_root_connections.csv",
        help="Output path",
    )
    args = parser.parse_args()

    analyze_post_root_morphemes(args.verbs, args.morphemes, args.output)
