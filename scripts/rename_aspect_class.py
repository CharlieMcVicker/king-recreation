#!/usr/bin/env python3
"""
CLI script to rename aspect classes using exact (class, subclass) tuples across data/classes.csv and curated files.

Target Files and Columns:
- data/classes.csv (class, subclass)
- curated/aspect_class_mascots.csv (class, subclass)
- curated/validated_reconstructable_roots.csv (class - formatted as "class-subclass" or "class")
- curated/stative_shims.csv (class - formatted as "class-subclass" or "class")
- curated/root_ids.csv (class - formatted as "class-subclass" or "class")
- curated/derivational_suffix_connections.csv (from_class, to_class - formatted as "class-subclass" or "class")

Tuples format:
  Old tuple: (old_class, old_subclass)
  New tuple: (new_class, new_subclass)

  If old_subclass is "" or None, it represents a base class without subclass.
  When joined in documents, class and subclass are joined with "-" (e.g. ("sg-s", "hi-hihst") -> "sg-s-hi-hihst").

Usage Examples:
  # Single rename:
  python scripts/rename_aspect_class.py --old-class sk-h --old-subclass yh --new-class sg-h --new-subclass yh

  # Clear subclass or rename base class only:
  python scripts/rename_aspect_class.py --old-class sk-h --new-class sg-h

  # Batch rename using JSON mapping file:
  # JSON structure:
  # [
  #   {
  #     "old": ["sk-h", "yh"],
  #     "new": ["sg-h", "yh"]
  #   },
  #   {
  #     "old": ["sk-h", ""],
  #     "new": ["sg-h", ""]
  #   }
  # ]
  python scripts/rename_aspect_class.py --mapping mappings.json --dry-run
"""

import argparse
import csv
import json
import os
import sys
from typing import Dict, List, Optional, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# List of files and whether they use split (class, subclass) columns vs joined "class" strings
FILES_SPEC = [
    {
        "path": os.path.join(REPO_ROOT, "data", "classes.csv"),
        "type": "split",
        "columns": ("class", "subclass"),
    },
    {
        "path": os.path.join(REPO_ROOT, "data", "post_root_morphemes.csv"),
        "type": "joined",
        "columns": ["classes"],
    },
    {
        "path": os.path.join(REPO_ROOT, "curated", "aspect_class_mascots.csv"),
        "type": "joined",
        "columns": ["class"],
    },
    {
        "path": os.path.join(
            REPO_ROOT, "curated", "validated_reconstructable_roots.csv"
        ),
        "type": "joined",
        "columns": ["class"],
    },
    {
        "path": os.path.join(REPO_ROOT, "curated", "stative_shims.csv"),
        "type": "joined",
        "columns": ["class"],
    },
    {
        "path": os.path.join(REPO_ROOT, "curated", "root_ids.csv"),
        "type": "joined",
        "columns": ["class"],
    },
    {
        "path": os.path.join(
            REPO_ROOT, "curated", "derivational_suffix_connections.csv"
        ),
        "type": "joined",
        "columns": ["from_class", "to_class"],
    },
]


def join_tuple(cls: str, subcls: Optional[str]) -> str:
    """Joins class and subclass into a single string with '-' if subclass exists."""
    c = cls.strip() if cls else ""
    s = subcls.strip() if subcls else ""
    return f"{c}-{s}" if s else c


def parse_joined_string(joined: str) -> Tuple[str, str, str]:
    """
    Parses a joined string like 'sg-s-hi-hihst[perf2]' into (base_str, tag_str).
    Example: 'sg-s-hi-hihst[perf2]' -> base='sg-s-hi-hihst', tag='[perf2]'
    """
    if "[" in joined:
        idx = joined.index("[")
        return joined[:idx], joined[idx:]
    return joined, ""


class ParentClassGroupRule:
    """
    Represents a major class rename rule for a parent class (e.g., old='hvsk', new='hvsg'),
    along with optional specific subclass renames (e.g., {'nh': 'hn'}).
    """

    def __init__(
        self,
        old_class: str,
        new_class: str,
        subclasses_map: Optional[Dict[str, str]] = None,
    ):
        self.old_class = old_class.strip()
        self.new_class = new_class.strip()
        # Map of old_subclass -> new_subclass
        self.subclasses_map = {
            k.strip(): v.strip() for k, v in (subclasses_map or {}).items()
        }

    def matches_split(self, cls_val: str, subcls_val: str) -> bool:
        """Matches if parent class matches."""
        c = (cls_val or "").strip()
        return c == self.old_class

    def transform_split(self, cls_val: str, subcls_val: str) -> Tuple[str, str]:
        """Transforms split class and subclass columns."""
        s = (subcls_val or "").strip()
        new_c = self.new_class
        new_s = self.subclasses_map.get(s, s)
        return new_c, new_s

    def matches_joined(self, joined_val: str) -> bool:
        """Matches if joined base string starts with old_class."""
        base_val, _ = parse_joined_string(joined_val.strip())
        if base_val == self.old_class:
            return True
        if base_val.startswith(f"{self.old_class}-"):
            return True
        return False

    def transform_joined(self, joined_val: str) -> str:
        """Transforms joined class string (e.g., 'hvsk-nh[perf2]' -> 'hvsg-hn[perf2]')."""
        base_val, tag = parse_joined_string(joined_val.strip())

        if base_val == self.old_class:
            # Base class without subclass (or empty subclass mapped)
            new_subcls = self.subclasses_map.get("", "")
            new_base = join_tuple(self.new_class, new_subcls)
            return f"{new_base}{tag}"

        if base_val.startswith(f"{self.old_class}-"):
            subcls = base_val[len(self.old_class) + 1 :]
            new_subcls = self.subclasses_map.get(subcls, subcls)
            new_base = join_tuple(self.new_class, new_subcls)
            return f"{new_base}{tag}"

        return joined_val


def process_split_file(
    file_path: str,
    cls_col: str,
    subcls_col: str,
    rules: List[ParentClassGroupRule],
    dry_run: bool = False,
) -> int:
    """Processes CSV files with separate class and subclass columns."""
    if not os.path.exists(file_path):
        print(f"[WARNING] File not found: {os.path.relpath(file_path, REPO_ROOT)}")
        return 0

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            return 0
        rows = list(reader)

    replaced_count = 0
    file_changed = False

    for row in rows:
        c_val = row.get(cls_col, "")
        s_val = row.get(subcls_col, "")

        for rule in rules:
            if rule.matches_split(c_val, s_val):
                new_c, new_s = rule.transform_split(c_val, s_val)
                if new_c != c_val or new_s != s_val:
                    row[cls_col] = new_c
                    row[subcls_col] = new_s
                    replaced_count += 1
                    file_changed = True
                    break

    if file_changed and not dry_run:
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return replaced_count


def process_joined_file(
    file_path: str,
    target_cols: List[str],
    rules: List[ParentClassGroupRule],
    dry_run: bool = False,
) -> Dict[str, int]:
    """Processes CSV files with joined class strings."""
    col_counts = {col: 0 for col in target_cols}
    if not os.path.exists(file_path):
        print(f"[WARNING] File not found: {os.path.relpath(file_path, REPO_ROOT)}")
        return col_counts

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            return col_counts
        rows = list(reader)

    file_changed = False

    for row in rows:
        for col in target_cols:
            val = row.get(col, "")
            if not val:
                continue

            # Support semicolon-separated items (e.g. "hih-hil;hih-hil[imp2]" or "g-ts[*]")
            items = val.split(";")
            new_items = []
            item_changed = False

            for item in items:
                item_str = item.strip()
                replaced = False
                for rule in rules:
                    if rule.matches_joined(item_str):
                        new_item = rule.transform_joined(item_str)
                        if new_item != item_str:
                            new_items.append(new_item)
                            replaced = True
                            item_changed = True
                            break
                if not replaced:
                    new_items.append(item_str)

            if item_changed:
                row[col] = ";".join(new_items)
                col_counts[col] += 1
                file_changed = True

    if file_changed and not dry_run:
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return col_counts


def rename_aspect_classes(
    rules: List[ParentClassGroupRule], dry_run: bool = False
) -> Dict[str, Dict[str, int]]:
    """Renames aspect classes using parent group rules across all target files."""
    results = {}

    for spec in FILES_SPEC:
        file_path = spec["path"]
        rel_path = os.path.relpath(file_path, REPO_ROOT)

        if spec["type"] == "split":
            cls_col, subcls_col = spec["columns"]
            count = process_split_file(
                file_path, cls_col, subcls_col, rules, dry_run=dry_run
            )
            results[rel_path] = {f"{cls_col},{subcls_col}": count}
        else:
            target_cols = spec["columns"]
            counts = process_joined_file(file_path, target_cols, rules, dry_run=dry_run)
            results[rel_path] = counts

    return results


def parse_mapping_file(mapping_path: str) -> List[ParentClassGroupRule]:
    """
    Parses JSON/CSV mapping file into a list of ParentClassGroupRules.
    """
    rules = []
    with open(mapping_path, "r", encoding="utf-8") as f:
        if mapping_path.endswith(".json"):
            data = json.load(f)
            if isinstance(data, list):
                for item in data:
                    if isinstance(item.get("old"), str) and isinstance(
                        item.get("new"), str
                    ):
                        parent_old = item["old"].strip()
                        parent_new = item["new"].strip()
                        subclasses = item.get("subclasses") or {}
                        rules.append(
                            ParentClassGroupRule(parent_old, parent_new, subclasses)
                        )
                    elif isinstance(item.get("old"), list) and isinstance(
                        item.get("new"), list
                    ):
                        old_c, old_s = item["old"][0], (
                            item["old"][1] if len(item["old"]) > 1 else ""
                        )
                        new_c, new_s = item["new"][0], (
                            item["new"][1] if len(item["new"]) > 1 else ""
                        )
                        rules.append(ParentClassGroupRule(old_c, new_c, {old_s: new_s}))
    return rules


def main():
    parser = argparse.ArgumentParser(
        description="Rename aspect classes using parent class groups and subclass mappings across data and curated files."
    )
    parser.add_argument("--old-class", type=str, help="Old class name")
    parser.add_argument(
        "--old-subclass", type=str, default="", help="Old subclass name (optional)"
    )
    parser.add_argument("--new-class", type=str, help="New class name")
    parser.add_argument(
        "--new-subclass", type=str, default="", help="New subclass name (optional)"
    )
    parser.add_argument(
        "--mapping",
        type=str,
        help="Path to JSON mapping file",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )

    args = parser.parse_args()

    rules = []
    if args.mapping:
        rules = parse_mapping_file(args.mapping)
    elif args.old_class and args.new_class:
        sub_map = (
            {args.old_subclass: args.new_subclass}
            if (args.old_subclass or args.new_subclass)
            else {}
        )
        rules = [ParentClassGroupRule(args.old_class, args.new_class, sub_map)]
    else:
        parser.error("Must specify either --old-class and --new-class, or --mapping")

    if not rules:
        print("No valid rename rules specified.")
        sys.exit(0)

    mode_str = " (DRY RUN)" if args.dry_run else ""
    print(f"--- Renaming Aspect Classes{mode_str} ---")
    for r in rules:
        print(f"  Parent Class: '{r.old_class}' -> '{r.new_class}'")
        if r.subclasses_map:
            for s_old, s_new in r.subclasses_map.items():
                old_label = s_old if s_old else "(base)"
                new_label = s_new if s_new else "(base)"
                print(f"    Subclass: '{old_label}' -> '{new_label}'")
        else:
            print("    (Renaming parent class across all subclasses)")
    print()

    results = rename_aspect_classes(rules, dry_run=args.dry_run)

    total_replacements = 0
    for rel_path, col_counts in results.items():
        subtotal = sum(col_counts.values())
        total_replacements += subtotal
        col_str = ", ".join([f"{col}: {cnt}" for col, cnt in col_counts.items()])
        print(f"{rel_path:<50} -> Total: {subtotal} ({col_str})")

    print(f"\nTotal replacements across all files: {total_replacements}")


if __name__ == "__main__":
    main()
