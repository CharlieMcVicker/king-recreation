import csv
from dataclasses import asdict, dataclass
from typing import List, Optional


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
