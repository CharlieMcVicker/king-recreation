import csv
import json
import os
from typing import Any, Dict, List, Tuple

from king_recreation.paths import (
    DERIVATIONAL_CONNECTIONS_PATH,
    HIERARCHICAL_DICT_PATH,
    ROOT_IDS_PATH,
)
from king_recreation.utils import load_root_ids_map


def load_derivational_connections() -> List[Dict[str, str]]:
    if not os.path.exists(DERIVATIONAL_CONNECTIONS_PATH):
        return []
    with open(DERIVATIONAL_CONNECTIONS_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_root_ids_overrides() -> Dict[str, str]:
    return load_root_ids_map(ROOT_IDS_PATH)


def save_root_ids(csv_rows: List[Dict], fieldnames: List[str]):
    os.makedirs(os.path.dirname(ROOT_IDS_PATH), exist_ok=True)
    with open(ROOT_IDS_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_rows)


def load_root_ids() -> List[Dict]:
    if not os.path.exists(ROOT_IDS_PATH):
        return []
    with open(ROOT_IDS_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_hierarchical_dict(data: Any, encoder_cls):
    os.makedirs(os.path.dirname(HIERARCHICAL_DICT_PATH), exist_ok=True)
    with open(HIERARCHICAL_DICT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, cls=encoder_cls)
    print(f"Hierarchical dictionary saved to {HIERARCHICAL_DICT_PATH}")


def load_hierarchical_dict() -> Any:
    if not os.path.exists(HIERARCHICAL_DICT_PATH):
        return None
    with open(HIERARCHICAL_DICT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)
