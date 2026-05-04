import csv
import os
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional

from king_recreation.paths import CORPUS_NO_ASP_PATH, MATCHES_PATH


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


def save_matches(matches_data: List[Dict[str, str]]):
    fieldnames = [
        "corpus_id",
        "definition",
        "class",
    ]
    with open(MATCHES_PATH, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches_data)
    print(f"Matches written to {MATCHES_PATH}")


def load_matches() -> List[Dict[str, str]]:
    if not os.path.exists(MATCHES_PATH):
        return []
    with open(MATCHES_PATH, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_stripped_corpus(data: List[StrippedVerbRow]):
    StrippedVerbRow.write_csv(CORPUS_NO_ASP_PATH, data)
    print(f"Endings Stripped Corpus written to {CORPUS_NO_ASP_PATH}")


def load_stripped_corpus() -> List[Dict[str, str]]:
    if not os.path.exists(CORPUS_NO_ASP_PATH):
        return []
    with open(CORPUS_NO_ASP_PATH, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))
