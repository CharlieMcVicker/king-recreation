import atexit
import csv
import json
import os
import time
from functools import partial, wraps
from typing import Dict, List, Optional, Tuple

from king_recreation.reconstruction import ReconstructableVerb


class track_performance:
    def __init__(self, func):
        wraps(func)(self)
        self.func = func
        self.total_time = 0
        self.call_count = 0
        # Register the report method to run when the script ends
        atexit.register(self.print_report)

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return partial(self, obj)

    def __call__(self, *args, **kwargs):
        start = time.perf_counter()
        result = self.func(*args, **kwargs)
        end = time.perf_counter()

        # Accumulate stats from "natural" execution
        self.total_time += end - start
        self.call_count += 1
        return result

    def print_report(self):
        if self.call_count > 0:
            avg = self.total_time / self.call_count
            print(f"\n--- Final Performance Report: {self.func.__name__} ---")
            print(f"Total Calls:   {self.call_count}")
            print(f"Total Time:    {self.total_time:.6f}s")
            print(f"Average Time:  {avg:.6f}s")


def load_verbs(verbs_json_path: str):
    """Loads reconstructable verbs from a JSON file."""

    if not os.path.exists(verbs_json_path):
        return []

    with open(verbs_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return [ReconstructableVerb.from_dict(item) for item in data]


def load_root_ids_map(root_ids_path: str) -> Dict[str, str]:
    """Loads a mapping of corpus_id -> root_id from the CSV, respecting user edits."""
    overrides = {}
    if not os.path.exists(root_ids_path):
        return overrides

    with open(root_ids_path, "r", encoding="utf-8") as f:
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


def group_verbs_by_root(
    verbs: List, root_id_overrides: Optional[Dict[str, str]] = None
) -> Dict[Tuple[str, str, str], Dict]:
    """Groups ReconstructableVerb objects by (root_id, class, stem_type)."""
    root_groups: Dict[Tuple[str, str, str], Dict] = {}
    root_id_overrides = root_id_overrides or {}

    for verb in verbs:
        stem_type = verb.config.pron.stem_type.value

        # Determine Root ID
        root_id = f"{verb.h_grade_root}|{verb.glottal_grade_root or ''}"
        if verb.corpus_id is not None:
            cid = str(verb.corpus_id)
        if cid in root_id_overrides:
            root_id = root_id_overrides[cid]

        # root_ids do not override h_grade; we track root_id as the grouping key.
        # We no longer parse h/g from the root_id.

        key = (
            root_id,
            verb.class_name,
            stem_type,
        )
        if key not in root_groups:
            root_groups[key] = {
                "root_id": root_id,
                "h_grade": verb.h_grade_root,
                "g_grade": verb.glottal_grade_root or "",
                "class": verb.class_name,
                "stem_type": stem_type,
                "corpus_ids": [],
                "verbs": [],
            }
        root_groups[key]["corpus_ids"].append(str(verb.corpus_id))
        root_groups[key]["verbs"].append(verb)
    return root_groups


def save_root_mapping(root_groups: Dict, path: str):
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
        path,
        ["root_id", "h_grade", "g_grade", "class", "stem_type", "corpus_ids"],
        mapping_rows,
    )


def load_existing_approvals(csv_path: str, key_fields: List[str]) -> Dict[Tuple, str]:
    """Loads user_approved flags from an existing CSV file."""
    approvals = {}
    if os.path.exists(csv_path) and csv_path.endswith(".csv"):
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                key = tuple(row.get(field, "") for field in key_fields)
                approvals[key] = row.get("user_approved", "")
    return approvals


def save_csv_artifact(path: str, fieldnames: List[str], rows: List[Dict]):
    """Saves a list of dictionaries to a CSV artifact, ensuring the directory exists."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
