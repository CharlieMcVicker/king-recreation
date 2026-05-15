import csv
import os
from dataclasses import asdict, dataclass

from dictionary_pipeline.paths import CORPUS_NO_ASP_PATH, MATCHES_PATH
from dictionary_pipeline.row_models import (
    AspectInfo,
    CorpusForms,
    RowModelBase,
    VerbMeta,
)


@dataclass
class StrippedVerbRow(RowModelBase):
    meta: VerbMeta
    aspect: AspectInfo
    forms: CorpusForms

    def copy(self):
        return StrippedVerbRow(
            meta=VerbMeta(**asdict(self.meta)),
            aspect=AspectInfo(**asdict(self.aspect)),
            forms=CorpusForms(**asdict(self.forms)),
        )


def save_matches(matches_data: list[dict[str, str]]) -> None:
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


def load_matches() -> list[dict[str, str]]:
    if not os.path.exists(MATCHES_PATH):
        return []
    with open(MATCHES_PATH, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_stripped_corpus(data: list[StrippedVerbRow]) -> None:
    StrippedVerbRow.write_csv(CORPUS_NO_ASP_PATH, data)
    print(f"Endings Stripped Corpus written to {CORPUS_NO_ASP_PATH}")


def load_stripped_corpus() -> list[dict[str, str]]:
    if not os.path.exists(CORPUS_NO_ASP_PATH):
        return []
    with open(CORPUS_NO_ASP_PATH, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))
