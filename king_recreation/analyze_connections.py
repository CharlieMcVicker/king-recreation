import json
import os
import csv
from typing import List, Dict, Set, Tuple
from king_recreation.reconstruct_from_roots import (
    ReconstructibleVerb,
    ReconstructionEngine,
    VerbConfig,
)
from king_recreation.phonology_data import (
    possible_alternates,
    prevent_C_glottal_cluster,
    PrePronominalConfig,
    PronominalConfig,
    StemType,
    MetathesisStrategy,
)


def analyze_connections(input_path: str, output_path: str, classes_path: str = None):
    if not os.path.exists(input_path):
        print(f"Error: Input file {input_path} not found.")
        return

    # Load existing approvals if they exist
    existing_approvals: Dict[Tuple[str, str, str, str, str, str], str] = {}
    if os.path.exists(output_path) and output_path.endswith(".csv"):
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Key: (from_h, from_class, to_h, to_class, to_type, to_stem)
                key = (
                    row.get("from_h_grade", ""),
                    row.get("from_class", ""),
                    row.get("to_h_grade", ""),
                    row.get("to_class", ""),
                    row.get("to_form_type", ""),
                    row.get("to_stem", ""),
                )
                existing_approvals[key] = row.get("user_approved", "")

    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    verbs: List[ReconstructibleVerb] = [
        ReconstructibleVerb.from_dict(item) for item in data
    ]

    # Group verbs by (h_grade, g_grade, class)
    root_groups: Dict[Tuple[str, str, str], Dict] = {}
    for verb in verbs:
        key = (verb.h_grade_root, verb.glottal_grade_root or "", verb.class_name)
        if key not in root_groups:
            root_groups[key] = {
                "h_grade": verb.h_grade_root,
                "g_grade": verb.glottal_grade_root or "",
                "class": verb.class_name,
                "corpus_ids": [],
                "verbs": [],
            }
        root_groups[key]["corpus_ids"].append(str(verb.corpus_id))
        root_groups[key]["verbs"].append(verb)

    # Write roots_by_class.csv
    csv_mapping_path = "artifacts/data/roots_by_class.csv"
    os.makedirs(os.path.dirname(csv_mapping_path), exist_ok=True)
    with open(csv_mapping_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f, fieldnames=["h_grade", "g_grade", "class", "corpus_ids"]
        )
        writer.writeheader()
        for key in sorted(root_groups.keys()):
            group = root_groups[key]
            writer.writerow(
                {
                    "h_grade": group["h_grade"],
                    "g_grade": group["g_grade"],
                    "class": group["class"],
                    "corpus_ids": ";".join(group["corpus_ids"]),
                }
            )

    engine = ReconstructionEngine(classes_path)

    # Map of (stem) -> List of root group info
    open_forms_map: Dict[str, List[Dict]] = {}

    for key, group in root_groups.items():
        if group["class"].startswith("stative"):
            continue
        # We use the first verb in the group to get base stems
        # since they share the same root and class
        sample_verb = group["verbs"][0]
        for form_type in ["perfective", "infinitive"]:
            base_stems = engine.get_base_stems_for_form(sample_verb, form_type)
            if not base_stems:
                continue

            for stem in base_stems:
                if stem not in open_forms_map:
                    open_forms_map[stem] = []

                open_forms_map[stem].append(
                    {
                        "corpus_ids": ";".join(group["corpus_ids"]),
                        "h_grade": group["h_grade"],
                        "g_grade": group["g_grade"],
                        "class_name": group["class"],
                        "form_type": form_type,
                        "stem": stem,
                    }
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
        "to_form_type",
        "to_stem",
    ]

    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    rows = []
    for key, group in root_groups.items():
        # Check against h_grade root
        root = group["h_grade"]
        if not root:
            continue

        if root in open_forms_map:
            for m in open_forms_map[root]:
                # Avoid self-reference: if the matched group is the current group
                if (m["h_grade"], m["g_grade"], m["class_name"]) == key:
                    continue

                # Heuristic logic
                is_cause = group["class"].startswith("cause")
                if is_cause or m["form_type"] == "perfective":
                    # Determine existing approval status
                    approval_key = (
                        group["h_grade"],
                        group["class"],
                        m["h_grade"],
                        m["class_name"],
                        m["form_type"],
                        m["stem"],
                    )
                    user_approved = existing_approvals.get(approval_key, "")

                    rows.append(
                        {
                            "user_approved": user_approved,
                            "from_h_grade": group["h_grade"],
                            "from_g_grade": group["g_grade"],
                            "from_class": group["class"],
                            "from_corpus_ids": ";".join(group["corpus_ids"]),
                            "to_h_grade": m["h_grade"],
                            "to_g_grade": m["g_grade"],
                            "to_class": m["class_name"],
                            "to_corpus_ids": m["corpus_ids"],
                            "to_form_type": m["form_type"],
                            "to_stem": m["stem"],
                        }
                    )

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    with open("artifacts/reports/open_forms.json", "w", encoding="utf-8") as f:
        json.dump(open_forms_map, f, indent=4, sort_keys=True)

    print(
        f"Analyzed {len(root_groups)} root groups ({len(verbs)} verbs). Found {len(rows)} connections."
    )
    print(f"Results written to {output_path}")
    print(f"Root-class mapping written to {csv_mapping_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze root connections.")
    parser.add_argument(
        "--input",
        default="artifacts/data/reconstructable_verbs.json",
        help="Path to reconstructable verbs JSON",
    )
    parser.add_argument(
        "--output",
        default="artifacts/data/root_connections.csv",
        help="Path to output CSV",
    )
    parser.add_argument("--classes", help="Path to classes CSV")
    args = parser.parse_args()

    analyze_connections(args.input, args.output, args.classes)
