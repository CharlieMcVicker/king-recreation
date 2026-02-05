import csv
from dataclasses import asdict, dataclass
from typing import List, Optional

from king_recreation.h_alternation import (
    possible_alternates,
    prevent_C_glottal_cluster,
    recreate_C_glottal_clusters,
)


@dataclass
class StrippedVerbRow:
    corpus_id: str
    definition: str
    verb_class: str
    post_root_morpheme: Optional[str] = None
    present: str = ""
    present_1sg: str = ""
    imperfective: str = ""
    perfective: str = ""
    imperative: str = ""
    infinitive: str = ""

    @staticmethod
    def dict_keys():
        return [
            "corpus_id",
            "definition",
            "class",
            "post_root_morpheme",
            "present",
            "present_1sg",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]

    @staticmethod
    def write_csv(filename, data: List["StrippedVerbRow"]):
        stripped_dicts = [x.to_dict() for x in data]
        with open(filename, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=StrippedVerbRow.dict_keys())
            writer.writeheader()
            writer.writerows(stripped_dicts)

    def to_dict(self):
        d = asdict(self)
        d["class"] = d.pop("verb_class")
        return d

    def copy(self):
        return StrippedVerbRow(**asdict(self))


def create_stripped_row(verb, classes_map, verb_class) -> Optional[StrippedVerbRow]:
    # Create stripped row

    cls_info = classes_map.get(verb_class)
    if not cls_info:
        return None

    stripped_row = StrippedVerbRow(
        corpus_id=verb.get("corpus_id", ""),
        definition=verb.get("definition", ""),
        verb_class=verb_class,
    )

    # Strip suffixes
    forms = [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    for fn in forms:
        form_val = verb.get(fn)
        if not form_val:
            continue

        cls_pattern = cls_info.get(fn)
        if fn == "present_1sg" and not cls_pattern:
            cls_pattern = cls_info.get("present")

        if cls_pattern is None:
            cls_pattern = ""

        # Strip Literal Suffix
        literal_suffix = cls_pattern.replace("*", "").replace("@", "")

        if form_val.endswith(literal_suffix):
            stripped_stem = (
                form_val[: -len(literal_suffix)] if literal_suffix else form_val
            )
            setattr(stripped_row, fn, stripped_stem)

        # allow h alternates
        elif fn in ["present_1sg", "imperative"]:
            for hless_suffix in possible_alternates(literal_suffix, fix_clusters=False):
                fixed_hless_suffix = prevent_C_glottal_cluster(hless_suffix)
                if form_val.endswith(fixed_hless_suffix):
                    stripped_stem = (
                        form_val[: -len(fixed_hless_suffix)]
                        if fixed_hless_suffix
                        else form_val
                    )
                    setattr(stripped_row, fn, stripped_stem)
                elif hless_suffix.startswith("'"):
                    form_with_glottals = recreate_C_glottal_clusters(form_val)
                    if form_with_glottals.endswith(hless_suffix):
                        stripped_stem = (
                            form_with_glottals[: -len(hless_suffix)]
                            if hless_suffix
                            else form_with_glottals
                        )
                        setattr(
                            stripped_row, fn, prevent_C_glottal_cluster(stripped_stem)
                        )

    return stripped_row
