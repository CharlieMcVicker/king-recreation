import csv
import json
import os
from typing import List

from king_recreation.paths import RECONSTRUCTABLE_VERBS_PATH
from king_recreation.reconstruction import ReconstructableVerb


def save_reconstructable_verbs(data: list, encoder_cls):
    os.makedirs(os.path.dirname(RECONSTRUCTABLE_VERBS_PATH), exist_ok=True)
    with open(RECONSTRUCTABLE_VERBS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, cls=encoder_cls, indent=4)
    print(f"Artifacts saved to {RECONSTRUCTABLE_VERBS_PATH}")


def load_reconstructable_verbs() -> List[ReconstructableVerb]:
    if not os.path.exists(RECONSTRUCTABLE_VERBS_PATH):
        return []
    with open(RECONSTRUCTABLE_VERBS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [ReconstructableVerb.from_dict(item) for item in data]
