from typing import Tuple
import json
import os
from typing import List, Dict, Set
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

    verbs: List[ReconstructibleVerb] = []
    for item in data:
        # Reconstruct VerbConfig from nested dict
        if "config" in item:
            pre_data = item["config"].get("pre", {})
            pron_data = item["config"].get("pron", {})

            # Since from_row expects a flat row and we have nested structures,
            # we can manually construct it or fix how we call it.
            # However, VerbConfig(pre=..., pron=...) is easier
            pre = PrePronominalConfig(**pre_data)

            # PronominalConfig has an enum StemType and MetathesisStrategy
            if "stem_type" in pron_data:
                pron_data["stem_type"] = StemType(pron_data["stem_type"])
            if "metathesis_strategy" in pron_data:
                pron_data["metathesis_strategy"] = MetathesisStrategy(
                    pron_data["metathesis_strategy"]
                )

            pron = PronominalConfig(**pron_data)
            item["config"] = VerbConfig(pre=pre, pron=pron)
        verbs.append(ReconstructibleVerb(**item))

    engine = ReconstructionEngine(classes_path)

    # Map of (stem) -> List of (verb_id, form_type)
    open_forms_map: Dict[Tuple[str, str], List[Dict]] = {}

    for verb in verbs:
        for form_type in ["perfective", "infinitive"]:
            base_stems = engine.get_base_stems_for_form(verb, form_type)
            print(
                verb.corpus_id,
                verb.definition,
                verb.h_grade_root,
                verb.class_name,
                base_stems,
            )
            if not base_stems:
                continue

            for stem in base_stems:
                # Add the stem and its alternates
                # alternates = possible_alternates(stem)
                if stem not in open_forms_map:
                    open_forms_map[stem] = []

                open_forms_map[stem].append(
                    {
                        "verb_id": verb.corpus_id,
                        "entry_no": verb.entry_no,
                        "root": verb.h_grade_root,
                        "definition": verb.definition,
                        "class_name": verb.class_name,
                        "form_type": form_type,
                        "stem": stem,
                    }
                )

    connections = []
    for verb in verbs:
        root = verb.h_grade_root
        if root == "":
            continue
        if root in open_forms_map:
            # Filter out self-references (though rare it might happen if root is same as its own perf/inf)
            # Only allow cause to match infitives
            matches = [
                m
                for m in open_forms_map[root]
                if m["root"] != verb.h_grade_root
                and (
                    verb.class_name.startswith("cause")
                    or m["form_type"] == "perfective"
                )
            ]
            if matches:
                connections.append(
                    {
                        "verb_id": verb.corpus_id,
                        "entry_no": verb.entry_no,
                        "definition": verb.definition,
                        "class_name": verb.class_name,
                        "root": root,
                        "connected_to": matches,
                    }
                )

    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(connections, f, indent=4, sort_keys=True)

    with open("artifacts/reports/open_forms.json", "w", encoding="utf-8") as f:
        json.dump(open_forms_map, f, indent=4, sort_keys=True)

    print(f"Analyzed {len(verbs)} verbs. Found {len(connections)} connections.")
    print(f"Results written to {output_path}")


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
