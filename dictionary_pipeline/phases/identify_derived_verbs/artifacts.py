import csv
import json
import os
from typing import Any

from dictionary_pipeline.json_utils import EnhancedJSONEncoder
from dictionary_pipeline.paths import (
    DERIVATIONAL_CONNECTIONS_PATH,
    OPEN_FORMS_PATH,
    ROOT_IDS_PATH,
    ROOTS_BY_CLASS_PATH,
)


def load_root_overrides() -> dict[str, str]:
    """Loads a mapping of corpus_id -> root_id from the CSV, respecting user edits."""
    overrides = {}
    if not os.path.exists(ROOT_IDS_PATH):
        return overrides

    with open(ROOT_IDS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("user_edited") == "x":
                rid = row.get("root_id")
                if "corpus_ids" in row:
                    cids = [
                        x.strip()
                        for x in row.get("corpus_ids", "").split(";")
                        if x.strip()
                    ]
                    for cid in cids:
                        overrides[cid] = rid
                elif "corpus_id" in row:
                    overrides[row["corpus_id"]] = rid
    return overrides


def load_existing_approvals_data(key_fields: list[str]) -> dict[tuple[Any, ...], str]:
    """Loads user_approved flags from an existing CSV file."""
    approvals = {}
    if os.path.exists(DERIVATIONAL_CONNECTIONS_PATH):
        with open(DERIVATIONAL_CONNECTIONS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = tuple(row.get(field, "") for field in key_fields)
                approvals[key] = row.get("user_approved", "")
    return approvals


def save_root_mapping(root_groups: dict[Any, dict[str, Any]]) -> None:
    """Saves the root-to-class mapping to a CSV file."""
    mapping_rows = []
    for key in sorted(root_groups.keys()):
        group = root_groups[key]
        mapping_rows.append(
            {
                "root_id": group["root_id"],
                "h_grade": group["h_grade"],
                "g_grade": group["g_grade"],
                "class": group["class"],
                "stem_type": group["stem_type"],
                "corpus_ids": ";".join(group["corpus_ids"]),
            }
        )
    save_csv_artifact(
        ROOTS_BY_CLASS_PATH,
        ["root_id", "h_grade", "g_grade", "class", "stem_type", "corpus_ids"],
        mapping_rows,
    )


def load_root_mapping() -> list[dict[str, Any]]:
    if not os.path.exists(ROOTS_BY_CLASS_PATH):
        return []
    with open(ROOTS_BY_CLASS_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_derivational_connections(
    rows: list[dict[str, Any]], fieldnames: list[str]
) -> None:
    save_csv_artifact(DERIVATIONAL_CONNECTIONS_PATH, fieldnames, rows)


def load_derivational_connections() -> list[dict[str, Any]]:
    if not os.path.exists(DERIVATIONAL_CONNECTIONS_PATH):
        return []
    with open(DERIVATIONAL_CONNECTIONS_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_open_forms(open_forms_map: dict[str, Any]) -> None:
    os.makedirs(os.path.dirname(OPEN_FORMS_PATH), exist_ok=True)
    with open(OPEN_FORMS_PATH, "w", encoding="utf-8") as f:
        json.dump(open_forms_map, f, indent=4, sort_keys=True, cls=EnhancedJSONEncoder)


def load_open_forms() -> dict[str, Any]:
    if not os.path.exists(OPEN_FORMS_PATH):
        return {}
    with open(OPEN_FORMS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_csv_artifact(
    path: str, fieldnames: list[str], rows: list[dict[str, Any]]
) -> None:
    """Saves a list of dictionaries to a CSV artifact, ensuring the directory exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
