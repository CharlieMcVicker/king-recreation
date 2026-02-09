import json
import os
from typing import Dict, List, Set, Tuple

from king_recreation.paths import (
    derivational_connections_path,
    open_forms_report_path,
    reconstructable_verbs_path,
    roots_by_class_path,
)
from king_recreation.reconstruct_from_roots import ReconstructionEngine, desegment
from king_recreation.utils import (
    group_verbs_by_root,
    load_existing_approvals,
    load_verbs,
    save_csv_artifact,
)


def analyze_connections(
    input_path: str,
    output_path: str,
    classes_path: str = None,
    verbs: List = None,
    root_groups: Dict = None,
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
        "from_class",
        "to_h_grade",
        "to_class",
        "to_form_type",
        "to_stem",
    ]
    existing_approvals = load_existing_approvals(output_path, approval_key_fields)

    # Write roots_by_class.csv
    csv_mapping_path = roots_by_class_path
    from king_recreation.utils import save_root_mapping

    save_root_mapping(root_groups, csv_mapping_path)

    engine = ReconstructionEngine(classes_path)

    # Map of (stem) -> List of root group info
    open_forms_map: Dict[str, List[Dict]] = {}

    for key, group in root_groups.items():
        if group["class"].startswith("stative"):
            continue

        sample_verb = group["verbs"][0]
        for form_type in ["perfective", "infinitive"]:
            base_stems = engine.get_base_stems_for_form(sample_verb, form_type)
            if not base_stems:
                continue

            for stem in [desegment(s) for s in base_stems]:
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

    rows = []
    for key, group in root_groups.items():
        # Check against h_grade root
        root = group["h_grade"]
        if not root:
            continue

        if root in open_forms_map:
            for m in open_forms_map[root]:
                # Avoid self-reference
                if (m["h_grade"], m["g_grade"], m["class_name"]) == key:
                    continue

                # Heuristic logic
                is_cause = group["class"].startswith("cause")
                if is_cause or m["form_type"] == "perfective":
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
    save_csv_artifact(output_path, fieldnames, rows)

    with open(open_forms_report_path, "w", encoding="utf-8") as f:
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
        default=reconstructable_verbs_path,
        help="Path to reconstructable verbs JSON",
    )
    parser.add_argument(
        "--output",
        default=derivational_connections_path,
        help="Path to output CSV",
    )
    parser.add_argument("--classes", help="Path to classes CSV")
    args = parser.parse_args()

    analyze_connections(args.input, args.output, args.classes)
