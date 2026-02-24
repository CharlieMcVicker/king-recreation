import json
import os
from typing import List

from king_recreation.paths import (
    RECONSTRUCTABLE_VERBS_PATH,
    VERB_SELECTION_SNAPSHOT_CANONICAL_PATH,
    VERB_SELECTION_SNAPSHOT_VOLATILE_PATH,
)
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


def save_selection_snapshot(snapshot_data: list, encoder_cls=None):
    """
    Saves a snapshot of all options and selections for each verb.
    """
    os.makedirs(os.path.dirname(VERB_SELECTION_SNAPSHOT_VOLATILE_PATH), exist_ok=True)
    with open(VERB_SELECTION_SNAPSHOT_VOLATILE_PATH, "w", encoding="utf-8") as f:
        json.dump(snapshot_data, f, indent=4, sort_keys=True, cls=encoder_cls)
    print(f"Selection snapshot saved to {VERB_SELECTION_SNAPSHOT_VOLATILE_PATH}")


def commit_selection_snapshot():
    """
    Commits the volatile selection snapshot to the canonical data directory.
    """
    import shutil

    if not os.path.exists(VERB_SELECTION_SNAPSHOT_VOLATILE_PATH):
        print(
            f"Error: Volatile snapshot not found at {VERB_SELECTION_SNAPSHOT_VOLATILE_PATH}"
        )
        return

    os.makedirs(os.path.dirname(VERB_SELECTION_SNAPSHOT_CANONICAL_PATH), exist_ok=True)
    shutil.copy2(
        VERB_SELECTION_SNAPSHOT_VOLATILE_PATH, VERB_SELECTION_SNAPSHOT_CANONICAL_PATH
    )
    print(f"Selection snapshot committed to {VERB_SELECTION_SNAPSHOT_CANONICAL_PATH}")
