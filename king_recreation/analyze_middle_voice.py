import json
import os
import csv
from typing import List, Dict, Set, Tuple
from king_recreation.reconstruct_from_roots import ReconstructibleVerb


def analyze_middle_voice(input_path: str, output_path: str):
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    # Load existing approvals if they exist
    existing_approvals: Dict[Tuple[str, str, str, str, str, str], str] = {}
    if os.path.exists(output_path) and output_path.endswith(".csv"):
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Key: (from_h, from_g, from_class, to_h, to_g, prefix)
                # Using tuple key to match current row for preservation
                key = (
                    row.get("from_h_grade", ""),
                    row.get("from_g_grade", ""),
                    row.get("from_class", ""),
                    row.get("to_h_grade", ""),
                    row.get("to_g_grade", ""),
                    row.get("prefix_type", ""),
                )
                existing_approvals[key] = row.get("user_approved", "")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    verbs: List[ReconstructibleVerb] = [
        ReconstructibleVerb.from_dict(item) for item in data
    ]

    # Group verbs by (h_grade, g_grade, class)
    # We need to map (h, g) -> List of groups to find potential bases ignoring class?
    # User said: "all forms should match exactly for both h and glottal root... no other extra rules"
    # This implies we match h and g roots exactly. Class might differ.

    # 1. Group all verbs
    root_groups: Dict[Tuple[str, str, str], Dict] = {}

    # 2. Also build a lookup map for bases: (h_root, g_root) -> List[GroupDict]
    base_lookup: Dict[Tuple[str, str], List[Dict]] = {}

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

            base_key = (verb.h_grade_root, verb.glottal_grade_root or "")
            if base_key not in base_lookup:
                base_lookup[base_key] = []
            base_lookup[base_key].append(group)

        root_groups[key]["corpus_ids"].append(str(verb.corpus_id))

    rows = []

    # Prefixes to check
    # special pair: al, ali
    # normal pairs: at, ata, atat (match both h and g)
    normal_prefixes = ["at", "ata", "atat"]

    for key, group in root_groups.items():
        h_root = group["h_grade"]
        g_root = group["g_grade"]

        # Skip if roots are too short or empty
        if not h_root or not g_root:
            continue

        matched_bases = []
        prefix_type = ""

        # Check 'ali' special case
        # h_root starts with 'al', g_root starts with 'ali'
        if h_root.startswith("al") and g_root.startswith("ali"):
            pot_base_h = h_root[2:]
            pot_base_g = g_root[3:]

            # Look up if this base exists
            if (pot_base_h, pot_base_g) in base_lookup:
                matched_bases = base_lookup[(pot_base_h, pot_base_g)]
                prefix_type = "ali"

        # Check normal prefixes if no match yet
        if not matched_bases:
            for p in normal_prefixes:
                if h_root.startswith(p) and g_root.startswith(p):
                    pot_base_h = h_root[len(p) :]
                    pot_base_g = g_root[len(p) :]

                    if (pot_base_h, pot_base_g) in base_lookup:
                        matched_bases = base_lookup[(pot_base_h, pot_base_g)]
                        prefix_type = p
                        break

        if matched_bases:
            for base in matched_bases:
                # Avoid self-match (though unlikely with length diff)
                if base == group:
                    continue

                approval_key = (
                    group["h_grade"],
                    group["g_grade"],
                    group["class"],
                    base["h_grade"],
                    base["g_grade"],
                    prefix_type,
                )

                user_approved = existing_approvals.get(approval_key, "")

                rows.append(
                    {
                        "user_approved": user_approved,
                        "from_h_grade": group["h_grade"],
                        "from_g_grade": group["g_grade"],
                        "from_class": group["class"],
                        "from_corpus_ids": ";".join(group["corpus_ids"]),
                        "to_h_grade": base["h_grade"],
                        "to_g_grade": base["g_grade"],
                        "to_class": base["class"],
                        "to_corpus_ids": ";".join(base["corpus_ids"]),
                        "prefix_type": prefix_type,
                    }
                )

    # Sort rows for stability
    # Sort by from_h, from_class, to_h, to_class
    rows.sort(
        key=lambda x: (
            x["from_h_grade"],
            x["from_class"],
            x["to_h_grade"],
            x["to_class"],
        )
    )

    fieldnames = [
        "user_approved",
        "from_h_grade",
        "from_g_grade",
        "from_class",
        "from_corpus_ids",
        "to_h_grade",
        "to_g_grade",
        "to_class",
        "to_corpus_ids",
        "prefix_type",
    ]

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(
        f"Analyzed {len(root_groups)} root groups for middle voice. Found {len(rows)} candidates."
    )
    print(f"Results written to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze middle voice connections.")
    parser.add_argument(
        "--input",
        default="artifacts/data/reconstructable_verbs.json",
        help="Path to reconstructable verbs JSON",
    )
    parser.add_argument(
        "--output",
        default="artifacts/data/middle_voice_connections.csv",
        help="Path to output CSV",
    )
    args = parser.parse_args()

    analyze_middle_voice(args.input, args.output)
