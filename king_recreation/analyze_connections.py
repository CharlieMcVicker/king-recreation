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
    csv_path = "artifacts/data/roots_by_class.csv"
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
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

    connections = []
    for key, group in root_groups.items():
        # Check against h_grade root
        root = group["h_grade"]
        if not root:
            continue

        if root in open_forms_map:
            # Filter matches
            matches = []
            for m in open_forms_map[root]:
                # Avoid self-reference: if the matched group is the current group
                if (m["h_grade"], m["g_grade"], m["class_name"]) == key:
                    continue

                # Heuristic logic
                is_cause = group["class"].startswith("cause")
                if is_cause or m["form_type"] == "perfective":
                    matches.append(m)

            if matches:
                connections.append(
                    {
                        "corpus_ids": group["corpus_ids"],
                        "h_grade": group["h_grade"],
                        "g_grade": group["g_grade"],
                        "class_name": group["class"],
                        "connected_to": matches,
                    }
                )

    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(connections, f, indent=4, sort_keys=True)

    with open("artifacts/reports/open_forms.json", "w", encoding="utf-8") as f:
        json.dump(open_forms_map, f, indent=4, sort_keys=True)

    print(
        f"Analyzed {len(root_groups)} root groups ({len(verbs)} verbs). Found {len(connections)} connections."
    )
    print(f"Results written to {output_path}")
    print(f"Root-class mapping written to {csv_path}")


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
        default="artifacts/data/root_connections.json",
        help="Path to output JSON",
    )
    parser.add_argument("--classes", help="Path to classes CSV")
    args = parser.parse_args()

    analyze_connections(args.input, args.output, args.classes)
