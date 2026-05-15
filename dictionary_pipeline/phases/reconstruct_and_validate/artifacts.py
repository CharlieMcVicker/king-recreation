import csv
import json
import os
from dataclasses import dataclass
from typing import Any

from dictionary_pipeline.paths import (
    CONSISTENCY_ANALYSIS_PATH,
    RECONSTRUCTION_FAILURES_PATH,
    RECONSTRUCTION_REPORT_PATH,
    RECONSTRUCTION_VALIDATION_PATH,
    VALIDATED_MATCHES_PATH,
    VALIDATED_RECONSTRUCTABLE_ROOTS_PATH,
)


def load_existing_validated_roots() -> list[dict[str, Any]]:
    """
    Loads roots previously marked as user_selected.
    """
    if not os.path.exists(VALIDATED_RECONSTRUCTABLE_ROOTS_PATH):
        return []
    user_selected_rows = []
    with open(VALIDATED_RECONSTRUCTABLE_ROOTS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and "user_selected" in reader.fieldnames:
            for row in reader:
                if row.get("user_selected") == "x":
                    user_selected_rows.append(row)
    return user_selected_rows


def save_consistency_analysis(data: list[dict[str, Any]]) -> None:
    forms = [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    analysis_fields = [
        "definition",
        "assigned_class",
        "is_consistent",
        "mismatch_details",
    ] + [f"root_{fn}" for fn in forms]
    os.makedirs(os.path.dirname(CONSISTENCY_ANALYSIS_PATH), exist_ok=True)
    with open(CONSISTENCY_ANALYSIS_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=analysis_fields)
        writer.writeheader()
        writer.writerows(data)


def load_consistency_analysis() -> list[dict[str, Any]]:
    if not os.path.exists(CONSISTENCY_ANALYSIS_PATH):
        return []
    with open(CONSISTENCY_ANALYSIS_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_validated_matches(data: list[dict[str, Any]]) -> None:
    if not data:
        return
    keys = ["corpus_id", "definition", "class", "scope"]
    os.makedirs(os.path.dirname(VALIDATED_MATCHES_PATH), exist_ok=True)
    with open(VALIDATED_MATCHES_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows(data)


def load_validated_matches() -> list[dict[str, Any]]:
    if not os.path.exists(VALIDATED_MATCHES_PATH):
        return []
    with open(VALIDATED_MATCHES_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_reconstruction_report(data: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(RECONSTRUCTION_REPORT_PATH), exist_ok=True)
    with open(RECONSTRUCTION_REPORT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "definition",
                "class",
                "root",
                "success",
                "ambiguous_forms",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(data)


def load_reconstruction_report() -> list[dict[str, Any]]:
    if not os.path.exists(RECONSTRUCTION_REPORT_PATH):
        return []
    with open(RECONSTRUCTION_REPORT_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_reconstruction_validation(data: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(RECONSTRUCTION_VALIDATION_PATH), exist_ok=True)
    with open(RECONSTRUCTION_VALIDATION_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)


def load_reconstruction_validation() -> dict[str, Any]:
    if not os.path.exists(RECONSTRUCTION_VALIDATION_PATH):
        return {}
    with open(RECONSTRUCTION_VALIDATION_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


from dictionary_pipeline.row_models import (
    AspectInfo,
    RootInfo,
    RowModelBase,
    UserCurationInfo,
    VerbMeta,
)
from morphology.morphemes.prefixes import PrefixConfig


@dataclass
class ValidatedRootRow(RowModelBase):
    meta: VerbMeta
    curation: UserCurationInfo
    aspect: AspectInfo
    roots: RootInfo
    config: PrefixConfig
    metathesis_involved: bool = False
    segmented_forms: str = ""


def save_validated_roots(data: list[dict[str, Any]]) -> None:
    if not data:
        return

    rows = [ValidatedRootRow.from_row(d) for d in data]
    ValidatedRootRow.write_csv(VALIDATED_RECONSTRUCTABLE_ROOTS_PATH, rows)


def load_validated_roots() -> list[dict[str, Any]]:
    if not os.path.exists(VALIDATED_RECONSTRUCTABLE_ROOTS_PATH):
        return []
    with open(VALIDATED_RECONSTRUCTABLE_ROOTS_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_reconstruction_failures(data: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(RECONSTRUCTION_FAILURES_PATH), exist_ok=True)
    with open(RECONSTRUCTION_FAILURES_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["corpus_id", "definition", "class", "mismatch_details"],
        )
        writer.writeheader()
        writer.writerows(data)


def load_reconstruction_failures() -> list[dict[str, Any]]:
    if not os.path.exists(RECONSTRUCTION_FAILURES_PATH):
        return []
    with open(RECONSTRUCTION_FAILURES_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))
