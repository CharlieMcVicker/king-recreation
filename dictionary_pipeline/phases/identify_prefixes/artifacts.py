import csv
import os
from dataclasses import dataclass
from typing import Any

from dictionary_pipeline.paths import (
    CORPUS_NO_PRE_NO_ASP_PATH,
    PRE_PARSING_FAILURES_PATH,
)
from dictionary_pipeline.row_models import AspectInfo, RootInfo, RowModelBase, VerbMeta
from morphology.morphemes.prefixes import PrefixConfig


@dataclass
class StrippedRootRow(RowModelBase):
    meta: VerbMeta
    aspect: AspectInfo
    roots: RootInfo
    config: PrefixConfig
    metathesis_involved: bool = False


def save_stripped_roots(labeled_data: list[dict[str, Any]]) -> None:
    if not labeled_data:
        return

    # Convert to StrippedRootRow to ensure schema consistency
    rows = [StrippedRootRow.from_row(d) for d in labeled_data]
    StrippedRootRow.write_csv(CORPUS_NO_PRE_NO_ASP_PATH, rows)
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
