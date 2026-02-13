import json
import os
import re
from dataclasses import asdict, dataclass
from typing import Dict, List, Set, Tuple

from king_recreation.morphemes.middle_voice import MiddleVoice
from king_recreation.morphemes.prefixes.pronominals import StemType
from king_recreation.paths import (
    DERIVATIONAL_CONNECTIONS_PATH,
    OPEN_FORMS_REPORT_PATH,
    RECONSTRUCTABLE_VERBS_PATH,
    ROOT_IDS_PATH,
    ROOTS_BY_CLASS_PATH,
)
from king_recreation.reconstruction import ReconstructionEngine, desegment
from king_recreation.utils import (
    group_verbs_by_root,
    load_existing_approvals,
    load_root_ids_map,
    load_verbs,
    save_csv_artifact,
    save_root_mapping,
)


@dataclass
class Connection:
    user_approved: str
    from_root_id: str
    from_h_grade: str
    from_g_grade: str
    from_class: str
    from_stem_type: str
    from_corpus_ids: str
    to_root_id: str
    to_h_grade: str
    to_g_grade: str
    to_class: str
    to_stem_type: str
    to_corpus_ids: str
    to_form_type: str
    to_stem: str

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


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
        root_overrides = load_root_ids_map(ROOT_IDS_PATH)
        root_groups = group_verbs_by_root(verbs, root_id_overrides=root_overrides)

    # Load existing approvals
    approval_key_fields = [
        "from_root_id",
        "from_class",
        "from_stem_type",
        "to_root_id",
        "to_class",
        "to_stem_type",
        "to_form_type",
        "to_stem",
    ]
    existing_approvals = load_existing_approvals(output_path, approval_key_fields)

    # Write roots_by_class.csv
    csv_mapping_path = ROOTS_BY_CLASS_PATH

    save_root_mapping(root_groups, csv_mapping_path)

    engine = ReconstructionEngine(classes_path)

    # Map of (stem) -> List of root group info
    open_forms_map: Dict[str, List[Dict]] = {}

    for key, group in root_groups.items():
        if group["class"].startswith("stative"):
            continue

        sample_verb = group["verbs"][0]
        for form_type in ["perfective", "infinitive"]:
            original_class = sample_verb.class_name
            optns = [original_class]
            if "[" in original_class:
                optns.append(re.sub(r"(\[[^\[\]]*\])", "", original_class))
            for class_name in optns:
                sample_verb.class_name = class_name
                base_stems = engine.get_base_stems_for_form(sample_verb, form_type)
                if not base_stems:
                    continue

                # TODO don't use desegment here
                # get proper set of segments joined
                for stem in [
                    desegment(
                        s
                        if sample_verb.config.pron.middle_voice == MiddleVoice.NONE
                        else "-".join(s.split("-")[1:])
                    )
                    for s in base_stems
                ]:
                    if sample_verb.config.pron.stem_type == StemType.LONG_START:
                        stem = ":" + stem
                    if stem not in open_forms_map:
                        open_forms_map[stem] = []

                    open_forms_map[stem].append(
                        {
                            "corpus_ids": ";".join(group["corpus_ids"]),
                            "root_id": group["root_id"],
                            "h_grade": group["h_grade"],
                            "g_grade": group["g_grade"],
                            "class_name": class_name,
                            "stem_type": group["stem_type"],
                            "form_type": form_type,
                            "stem": stem,
                        }
                    )

            sample_verb.class_name = original_class

    connections: List[Connection] = []
    for key, group in root_groups.items():
        # Check against h_grade root
        root = group["h_grade"]
        if not root:
            continue

        if root in open_forms_map:
            for m in open_forms_map[root]:
                # Avoid self-reference
                if (
                    m["root_id"],
                    m["class_name"],
                    m["stem_type"],
                ) == key:
                    continue

                # Heuristic logic
                is_cause = group["class"].startswith("cause")
                if is_cause or m["form_type"] == "perfective":
                    approval_key = (
                        group["root_id"],
                        group["class"],
                        group["stem_type"],
                        m["root_id"],
                        m["class_name"],
                        m["stem_type"],
                        m["form_type"],
                        m["stem"],
                    )
                    user_approved = existing_approvals.get(approval_key, "")

                    connections.append(
                        Connection(
                            user_approved=user_approved,
                            from_root_id=group["root_id"],
                            from_h_grade=group["h_grade"],
                            from_g_grade=group["g_grade"],
                            from_class=group["class"],
                            from_stem_type=group["stem_type"],
                            from_corpus_ids=";".join(group["corpus_ids"]),
                            to_root_id=m["root_id"],
                            to_h_grade=m["h_grade"],
                            to_g_grade=m["g_grade"],
                            to_class=m["class_name"],
                            to_stem_type=m["stem_type"],
                            to_corpus_ids=m["corpus_ids"],
                            to_form_type=m["form_type"],
                            to_stem=m["stem"],
                        )
                    )

    fieldnames = [
        "user_approved",
        "from_root_id",
        "from_h_grade",
        "from_g_grade",
        "from_class",
        "from_stem_type",
        "from_corpus_ids",
        "to_root_id",
        "to_h_grade",
        "to_g_grade",
        "to_class",
        "to_stem_type",
        "to_corpus_ids",
        "to_form_type",
        "to_stem",
    ]

    rows = [c.to_dict() for c in connections]
    save_csv_artifact(
        output_path,
        fieldnames,
        sorted(
            rows,
            key=lambda row: tuple(
                row.get(fn)
                for fn in [
                    "to_root_id",
                    "to_h_grade",
                    "to_g_grade",
                    "to_class",
                    "to_stem_type",
                    "from_root_id",
                    "from_h_grade",
                    "from_g_grade",
                    "from_class",
                    "from_stem_type",
                    "user_approved",
                ]
            ),
        ),
    )

    with open(OPEN_FORMS_REPORT_PATH, "w", encoding="utf-8") as f:
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
        default=RECONSTRUCTABLE_VERBS_PATH,
        help="Path to reconstructable verbs JSON",
    )
    parser.add_argument(
        "--output",
        default=DERIVATIONAL_CONNECTIONS_PATH,
        help="Path to output CSV",
    )
    parser.add_argument("--classes", help="Path to classes CSV")
    args = parser.parse_args()

    analyze_connections(args.input, args.output, args.classes)
