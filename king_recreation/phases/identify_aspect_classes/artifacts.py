import csv
import os
from typing import Dict, List

from king_recreation.morphemes.aspect.class_patterns import StrippedVerbRow
from king_recreation.paths import CORPUS_NO_ASP_PATH, MATCHES_PATH


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
