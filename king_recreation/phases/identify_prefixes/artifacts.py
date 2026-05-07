import csv
import os
from typing import Any

from king_recreation.paths import CORPUS_NO_PRE_NO_ASP_PATH, PRE_PARSING_FAILURES_PATH


def save_stripped_roots(labeled_data: list[dict[str, Any]]) -> None:
    if not labeled_data:
        return

    form_names = [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    keys = labeled_data[0].keys()
    keys = [k for k in keys if k not in form_names]

    with open(CORPUS_NO_PRE_NO_ASP_PATH, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(
            {k: v for k, v in row.items() if k in keys} for row in labeled_data
        )
    print(f"Success: {len(labeled_data)}")


def load_stripped_roots() -> list[dict[str, Any]]:
    if not os.path.exists(CORPUS_NO_PRE_NO_ASP_PATH):
        return []
    with open(CORPUS_NO_PRE_NO_ASP_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_prefix_parsing_failures(failures: list[dict[str, Any]]) -> None:
    if not failures:
        return
    keys = failures[0].keys()
    with open(PRE_PARSING_FAILURES_PATH, "w", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(failures)
    print(f"Failures: {len(failures)}")


def load_prefix_parsing_failures() -> list[dict[str, Any]]:
    if not os.path.exists(PRE_PARSING_FAILURES_PATH):
        return []
    with open(PRE_PARSING_FAILURES_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))
