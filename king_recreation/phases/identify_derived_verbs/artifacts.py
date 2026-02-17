import csv
import json
import os
from typing import Any, Dict, List

from king_recreation.paths import (
    DERIVATIONAL_CONNECTIONS_PATH,
    OPEN_FORMS_PATH,
    ROOT_IDS_PATH,
    ROOTS_BY_CLASS_PATH,
)
from king_recreation.utils import (
    load_existing_approvals,
    load_root_ids_map,
    save_csv_artifact,
)
from king_recreation.utils import save_root_mapping as save_root_mapping_util


def load_root_overrides():
    return load_root_ids_map(ROOT_IDS_PATH)


def load_existing_approvals_data(key_fields):
    return load_existing_approvals(DERIVATIONAL_CONNECTIONS_PATH, key_fields)


def save_root_mapping(root_groups):
    save_root_mapping_util(root_groups, ROOTS_BY_CLASS_PATH)


def load_root_mapping():
    if not os.path.exists(ROOTS_BY_CLASS_PATH):
        return []
    with open(ROOTS_BY_CLASS_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_derivational_connections(rows, fieldnames):
    save_csv_artifact(DERIVATIONAL_CONNECTIONS_PATH, fieldnames, rows)


def load_derivational_connections() -> List[Dict]:
    if not os.path.exists(DERIVATIONAL_CONNECTIONS_PATH):
        return []
    with open(DERIVATIONAL_CONNECTIONS_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_open_forms(open_forms_map):
    os.makedirs(os.path.dirname(OPEN_FORMS_PATH), exist_ok=True)
    with open(OPEN_FORMS_PATH, "w", encoding="utf-8") as f:
        json.dump(open_forms_map, f, indent=4, sort_keys=True)


def load_open_forms() -> Dict:
    if not os.path.exists(OPEN_FORMS_PATH):
        return {}
    with open(OPEN_FORMS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
