#!/usr/bin/env python3
"""
Deep diff script to verify that the ONLY differences between two JSON files
(e.g., HEAD vs dirty working tree version of artifacts/data/hierarchical-dict.json)
are in class name fields ("class_name" or "class").

Usage:
  python scripts/verify_hierarchical_dict_diff.py [--file1 FILE1] [--file2 FILE2]

Defaults:
  FILE1: HEAD version of artifacts/data/hierarchical-dict.json (via git show HEAD:...)
  FILE2: Current working tree file artifacts/data/hierarchical-dict.json
"""

import argparse
import json
import os
import subprocess
import sys
from typing import Any, List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET_REL_PATH = "artifacts/data/hierarchical-dict.json"
ALLOWED_KEY_NAMES = {"class_name", "class"}


def load_json_from_git_head(rel_path: str) -> Any:
    """Loads JSON file content from git HEAD."""
    cmd = ["git", "show", f"HEAD:{rel_path}"]
    result = subprocess.run(
        cmd, cwd=REPO_ROOT, capture_output=True, text=True, check=True
    )
    return json.loads(result.stdout)


def normalize_class_names(data: Any) -> Any:
    """
    Recursively replaces all 'class_name' and 'class' values with a fixed placeholder '__CLASS_NAME__'.
    Strips 'shim' object as well.
    """
    if isinstance(data, dict):
        new_dict = {}
        for k, v in data.items():
            if k == "shim":
                continue
            if k in ALLOWED_KEY_NAMES:
                new_dict[k] = "__CLASS_NAME__"
            else:
                new_dict[k] = normalize_class_names(v)
        return new_dict
    elif isinstance(data, list):
        return [normalize_class_names(item) for item in data]
    else:
        return data


def index_hierarchical_dict(data: List[dict]) -> dict:
    """
    Indexes hierarchical dictionary by verb corpus_id for order-independent comparison.
    Value: normalized verb dict (with derivations field stripped for cross-connection stability).
    """
    verbs_by_id = {}
    for group in data:
        for cls_group in group.get("classes", []):
            for verb in cls_group.get("verbs", []):
                corpus_id = verb.get("meta", {}).get("corpus_id")
                if corpus_id:
                    verb_copy = json.loads(json.dumps(verb))
                    # Remove derivations list as it changes when derivational connections rename
                    verb_copy.pop("derivations", None)
                    verbs_by_id[corpus_id] = normalize_class_names(verb_copy)
    return verbs_by_id


def deep_diff(
    val1: Any,
    val2: Any,
    path: str = "$",
) -> List[Tuple[str, Any, Any]]:
    """
    Recursively compares two JSON structures ignoring class name differences.
    """
    unexpected_diffs = []

    if type(val1) is not type(val2):
        unexpected_diffs.append((path, val1, val2))
        return unexpected_diffs

    if isinstance(val1, dict):
        keys1 = set(val1.keys())
        keys2 = set(val2.keys())

        missing_in_2 = keys1 - keys2
        missing_in_1 = keys2 - keys1

        if missing_in_2:
            unexpected_diffs.append(
                (f"{path} (keys missing in target)", list(missing_in_2), None)
            )
        if missing_in_1:
            unexpected_diffs.append(
                (f"{path} (extra keys in target)", None, list(missing_in_1))
            )

        for k in keys1 & keys2:
            if k in ALLOWED_KEY_NAMES:
                continue
            sub_path = f"{path}.{k}"
            v1 = val1[k]
            v2 = val2[k]
            if v1 != v2:
                if isinstance(v1, (dict, list)):
                    unexpected_diffs.extend(deep_diff(v1, v2, sub_path))
                else:
                    unexpected_diffs.append((sub_path, v1, v2))

    elif isinstance(val1, list):
        if len(val1) != len(val2):
            unexpected_diffs.append((f"{path} (length mismatch)", len(val1), len(val2)))
            min_len = min(len(val1), len(val2))
            for i in range(min_len):
                unexpected_diffs.extend(deep_diff(val1[i], val2[i], f"{path}[{i}]"))
        else:
            for i in range(len(val1)):
                unexpected_diffs.extend(deep_diff(val1[i], val2[i], f"{path}[{i}]"))
    else:
        if val1 != val2:
            unexpected_diffs.append((path, val1, val2))

    return unexpected_diffs


def collect_class_changes(
    val1: Any, val2: Any, path: str = "$"
) -> List[Tuple[str, str, str]]:
    """
    Collects all class field changes: (json_path, old_class_name, new_class_name).
    """
    class_changes = []

    if isinstance(val1, dict) and isinstance(val2, dict):
        for k in val1.keys() & val2.keys():
            sub_path = f"{path}.{k}"
            v1 = val1[k]
            v2 = val2[k]

            if k in ALLOWED_KEY_NAMES and v1 != v2:
                class_changes.append((sub_path, str(v1), str(v2)))

            if isinstance(v1, (dict, list)) and isinstance(v2, type(v1)):
                class_changes.extend(collect_class_changes(v1, v2, sub_path))

    elif isinstance(val1, list) and isinstance(val2, list):
        min_len = min(len(val1), len(val2))
        for i in range(min_len):
            class_changes.extend(
                collect_class_changes(val1[i], val2[i], f"{path}[{i}]")
            )

    return class_changes


def verify_hierarchical_dict(file1_path: str = None, file2_path: str = None) -> bool:
    """
    Verifies that file2 matches file1 in structure and values except for class_name / class fields.
    """
    target_full_path = os.path.join(REPO_ROOT, TARGET_REL_PATH)

    if file1_path:
        print(f"Loading Base JSON: {file1_path}")
        with open(file1_path, "r", encoding="utf-8") as f:
            base_data = json.load(f)
    else:
        print(f"Loading Base JSON from git HEAD: {TARGET_REL_PATH}")
        base_data = load_json_from_git_head(TARGET_REL_PATH)

    if file2_path:
        print(f"Loading Target JSON: {file2_path}")
        with open(file2_path, "r", encoding="utf-8") as f:
            target_data = json.load(f)
    else:
        print(f"Loading Target JSON from working tree: {TARGET_REL_PATH}")
        with open(target_full_path, "r", encoding="utf-8") as f:
            target_data = json.load(f)

    print("Running deep structural diff...")

    # 1. Collect exact class changes
    class_changes = collect_class_changes(base_data, target_data)

    # 2. Build indexed maps of verbs by corpus_id
    base_verbs = index_hierarchical_dict(base_data)
    target_verbs = index_hierarchical_dict(target_data)

    unexpected_diffs = []

    base_cids = set(base_verbs.keys())
    target_cids = set(target_verbs.keys())

    missing_cids = base_cids - target_cids
    extra_cids = target_cids - base_cids

    if missing_cids:
        unexpected_diffs.append(
            ("Corpus IDs missing in target", list(missing_cids), None)
        )

    for cid in base_cids & target_cids:
        v_diffs = deep_diff(base_verbs[cid], target_verbs[cid], path=f"Verb[{cid}]")
        unexpected_diffs.extend(v_diffs)

    print("\n--- CLASS NAME CHANGES DETECTED ---")
    print(f"Total class name fields updated: {len(class_changes)}")
    for p, old_c, new_c in class_changes[:10]:
        print(f"  {p}: '{old_c}' -> '{new_c}'")
    if len(class_changes) > 10:
        print(f"  ... and {len(class_changes) - 10} more class changes.")

    print("\n--- NON-CLASS DIFFERENCES CHECK ---")
    if unexpected_diffs:
        print(f"[FAIL] Found {len(unexpected_diffs)} unexpected non-class differences!")
        for p, v1, v2 in unexpected_diffs[:20]:
            print(f"  Path: {p}")
            print(f"    HEAD:   {v1}")
            print(f"    TARGET: {v2}")
        if len(unexpected_diffs) > 20:
            print(f"  ... and {len(unexpected_diffs) - 20} more unexpected diffs.")
        return False
    else:
        print("[SUCCESS] All non-class fields are identical! Only class fields differ.")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Verify that hierarchical-dict.json dirty state differs from HEAD ONLY in class_name fields."
    )
    parser.add_argument(
        "--file1",
        type=str,
        help="Base JSON file (defaults to git HEAD:artifacts/data/hierarchical-dict.json)",
    )
    parser.add_argument(
        "--file2",
        type=str,
        help="Target JSON file (defaults to working tree artifacts/data/hierarchical-dict.json)",
    )

    args = parser.parse_args()
    success = verify_hierarchical_dict(file1_path=args.file1, file2_path=args.file2)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
