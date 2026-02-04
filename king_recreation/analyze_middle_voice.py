import os
from typing import List, Dict, Set, Tuple
from king_recreation.utils import (
    load_verbs,
    group_verbs_by_root,
    load_existing_approvals,
    save_csv_artifact,
)


def analyze_middle_voice(
    input_path: str, output_path: str, verbs: List = None, root_groups: Dict = None
):
    if verbs is None or root_groups is None:
        if not os.path.exists(input_path):
            print(f"Error: Input file {input_path} not found.")
            return
        verbs = load_verbs(input_path)
        root_groups = group_verbs_by_root(verbs)

    # Load existing approvals
    approval_key_fields = [
        "from_h_grade",
        "from_g_grade",
        "from_class",
        "to_h_grade",
        "to_g_grade",
        "prefix_type",
    ]
    existing_approvals = load_existing_approvals(output_path, approval_key_fields)

    # lookup map for bases: (h_root, g_root) -> List[GroupDict]
    base_lookup: Dict[Tuple[str, str], List[Dict]] = {}
    for group in root_groups.values():
        base_key = (group["h_grade"], group["g_grade"])
        if base_key not in base_lookup:
            base_lookup[base_key] = []
        base_lookup[base_key].append(group)

    rows = []

    # Prefixes to check
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
        if h_root.startswith("al") and g_root.startswith("ali"):
            pot_base_h = h_root[2:]
            pot_base_g = g_root[3:]

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
                # Avoid self-match
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

    # Sort rows
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
    save_csv_artifact(output_path, fieldnames, rows)

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
