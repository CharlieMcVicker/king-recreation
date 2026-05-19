import re
from dataclasses import dataclass
from typing import Any

from dictionary_pipeline.dictionary_forms import DictionaryVerb
from dictionary_pipeline.json_utils import to_dict
from dictionary_pipeline.phases.identify_derived_verbs.artifacts import (
    load_existing_approvals_data,
    load_root_overrides,
    save_derivational_connections,
    save_open_forms,
    save_root_mapping,
)
from dictionary_pipeline.phases.select_canonical_derivations.artifacts import (
    load_reconstructable_verbs,
)
from morphology.morphemes.prefixes.pronominals import MiddleVoice, StemType
from morphology.morphology_types import Aspect
from morphology.reconstruction import ReconstructionEngine, desegment


def group_verbs_by_root(
    verbs: list[DictionaryVerb], root_id_overrides: dict[str, str] | None = None
) -> dict[tuple[str, str, str], dict[str, Any]]:
    """Groups DictionaryVerb objects by (root_id, class, stem_type)."""
    root_groups: dict[tuple[str, str, str], dict[str, Any]] = {}
    root_id_overrides = root_id_overrides or {}

    for verb in verbs:
        stem_type = verb.morphology.config.pron.stem_type.value

        # Determine Root ID
        root_id = (
            f"{verb.morphology.h_grade_root}|{verb.morphology.glottal_grade_root or ''}"
        )
        if verb.corpus_id is not None:
            cid = str(verb.corpus_id)
            if cid in root_id_overrides:
                root_id = root_id_overrides[cid]

        # root_ids do not override h_grade; we track root_id as the grouping key.
        # We no longer parse h/g from the root_id.

        key = (
            root_id,
            verb.morphology.class_name,
            stem_type,
        )
        if key not in root_groups:
            root_groups[key] = {
                "root_id": root_id,
                "h_grade": verb.morphology.h_grade_root,
                "g_grade": verb.morphology.glottal_grade_root or "",
                "class": verb.morphology.class_name,
                "stem_type": stem_type,
                "corpus_ids": [],
                "verbs": [],
            }
        root_groups[key]["corpus_ids"].append(str(verb.corpus_id))
        root_groups[key]["verbs"].append(verb)

    for key in root_groups:
        root_groups[key]["corpus_ids"] = sorted(
            list(set(root_groups[key]["corpus_ids"])),
            key=lambda x: int(x) if x.isdigit() else 0,
        )
    return root_groups


@dataclass
class DerivedVerbConnection:
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DerivedVerbConnection":
        return cls(**data)


def identify_derived_verbs(
    classes_path: str | None = None,
) -> None:
    """
    Identify which validated verbs appear to be derived from other verbs.

    Inputs:
    * RECONSTRUCTABLE_VERBS_PATH: List of validated reconstructable verbs.
    * ROOT_IDS_PATH: Map of verb IDs to root IDs.

    Outputs:
    * DERIVATIONAL_CONNECTIONS_PATH: CSV of identified derivational connections.
    * OPEN_FORMS_PATH: JSON dump of potential derivation bases.
    * ROOTS_BY_CLASS_PATH: CSV mapping roots to classes.
    """
    verbs = load_reconstructable_verbs()
    if not verbs:
        print("Required inputs missing.")
        return
    root_overrides = load_root_overrides()
    root_groups = group_verbs_by_root(verbs, root_id_overrides=root_overrides)

    # Load existing approvals
    approval_key_fields = [
        "from_root_id",
        "from_class",
        "from_stem_type",
        "from_corpus_ids",
        "to_root_id",
        "to_class",
        "to_stem_type",
        "to_corpus_ids",
        "to_form_type",
        "to_stem",
    ]
    existing_approvals = load_existing_approvals_data(approval_key_fields)

    # Write roots_by_class.csv
    save_root_mapping(root_groups)

    engine = ReconstructionEngine(classes_path)

    # Map of (stem) -> list of root group info
    open_forms_map: dict[str, list[dict[str, Any]]] = {}

    for key, group in root_groups.items():
        if group["class"].startswith("stative"):
            continue

        sample_verb = group["verbs"][0]
        for aspect in [Aspect.PERFECTIVE, Aspect.INFINITIVE]:
            original_class = sample_verb.morphology.class_name
            optns = [original_class]
            if "[" in original_class:
                optns.append(re.sub(r"(\[[^\[\]]*\])", "", original_class))
            for class_name in optns:
                sample_verb.morphology.class_name = class_name
                base_stems = engine.get_base_stems_for_form(
                    sample_verb.morphology, aspect, glottal_grade=False
                )
                if not base_stems:
                    continue

                for stem in [
                    desegment(
                        s
                        if sample_verb.morphology.config.pron.middle_voice
                        == MiddleVoice.NONE
                        else "-".join(s.split("-")[1:])
                    )
                    for s in base_stems
                ]:
                    if (
                        sample_verb.morphology.config.pron.stem_type
                        == StemType.LONG_START
                    ):
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
                            "form_type": aspect.value,
                            "stem": stem,
                        }
                    )

            sample_verb.morphology.class_name = original_class

    connections: list[DerivedVerbConnection] = []
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
                        ";".join(group["corpus_ids"]),
                        m["root_id"],
                        m["class_name"],
                        m["stem_type"],
                        m["corpus_ids"],
                        m["form_type"],
                        m["stem"],
                    )
                    user_approved = existing_approvals.get(approval_key, "")

                    connections.append(
                        DerivedVerbConnection(
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

    rows = [to_dict(c) for c in connections]
    save_derivational_connections(
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
                    "to_form_type",
                    "to_stem",
                    "to_corpus_ids",
                    "from_corpus_ids",
                ]
            ),
        ),
        fieldnames,
    )

    save_open_forms(open_forms_map)

    print(f"Results written.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Analyze root connections.")
    parser.add_argument("--classes", help="Path to classes CSV")
    args = parser.parse_args()

    identify_derived_verbs(args.classes)
