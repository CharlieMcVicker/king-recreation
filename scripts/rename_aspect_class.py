#!/usr/bin/env python3
"""
CLI script to rename aspect classes across data/classes.csv and curated files.

Target Files and Columns:
- data/classes.csv (class column)
- curated/validated_reconstructable_roots.csv (class column)
- curated/stative_shims.csv (class column)
- curated/root_ids.csv (class column)
- curated/derivational_suffix_connections.csv (from_class, to_class columns)
- curated/aspect_class_mascots.csv (class column)

Supports bracketed subvariants, e.g. replacing 'old_name' will update:
- 'old_name' -> 'new_name'
- 'old_name[perf2]' -> 'new_name[perf2]'
- 'old_name[perf2-inf2]' -> 'new_name[perf2-inf2]'

Usage:
  # Single rename:
  python scripts/rename_aspect_class.py --old old_name --new new_name

  # Batch rename with JSON file:
  python scripts/rename_aspect_class.py --mapping mapping.json

  # Dry run (preview changes without writing):
  python scripts/rename_aspect_class.py --old old_name --new new_name --dry-run
"""

import argparse
import csv
import json
import os
import re
import sys
from typing import Dict, List, Tuple

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TARGET_SPECS: List[Tuple[str, List[str]]] = [
    (os.path.join(REPO_ROOT, "data", "classes.csv"), ["class"]),
    (
        os.path.join(REPO_ROOT, "curated", "validated_reconstructable_roots.csv"),
        ["class"],
    ),
    (os.path.join(REPO_ROOT, "curated", "stative_shims.csv"), ["class"]),
    (os.path.join(REPO_ROOT, "curated", "root_ids.csv"), ["class"]),
    (
        os.path.join(REPO_ROOT, "curated", "derivational_suffix_connections.csv"),
        ["from_class", "to_class"],
    ),
    (os.path.join(REPO_ROOT, "curated", "aspect_class_mascots.csv"), ["class"]),
]


def build_replacement_patterns(
    renames: Dict[str, str],
) -> List[Tuple[re.Pattern, str, str, str]]:
    """
    Builds compiled regex patterns for given class renames.
    Matches exact class name, hyphenated subclasses ('-subclass'), or bracketed subvariants ('[tag]').
    Returns list of (compiled_pattern, replacement, old_name, new_name).
    """
    patterns = []
    for old_name, new_name in renames.items():
        if not old_name or not new_name:
            continue
        # Pattern matches old_name at the start, followed by '-', '[', or end of string
        pattern = re.compile(rf"^{re.escape(old_name)}(?=-|\[|$)")
        patterns.append((pattern, new_name, old_name, new_name))
    return patterns


def replace_in_value(
    val: str, patterns: List[Tuple[re.Pattern, str, str, str]]
) -> Tuple[str, bool]:
    """
    Applies patterns to a cell value.
    Returns (new_val, changed_boolean).
    """
    if not val:
        return val, False

    for pattern, new_name, _, _ in patterns:
        if pattern.search(val):
            new_val = pattern.sub(new_name, val, count=1)
            return new_val, True

    return val, False


def process_file(
    file_path: str,
    target_columns: List[str],
    patterns: List[Tuple[re.Pattern, str, str, str]],
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Processes a single CSV file, replacing matching class names in specified columns.
    Returns a dict mapping column name to number of replacements made.
    """
    column_counts: Dict[str, int] = {col: 0 for col in target_columns}

    if not os.path.exists(file_path):
        print(
            f"[WARNING] File not found, skipping: {os.path.relpath(file_path, REPO_ROOT)}"
        )
        return column_counts

    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            return column_counts
        rows = list(reader)

    file_changed = False
    for row in rows:
        for col in target_columns:
            if col in row and row[col]:
                new_val, changed = replace_in_value(row[col], patterns)
                if changed:
                    row[col] = new_val
                    column_counts[col] += 1
                    file_changed = True

    if file_changed and not dry_run:
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    return column_counts


def rename_aspect_classes(
    renames: Dict[str, str], dry_run: bool = False
) -> Dict[str, Dict[str, int]]:
    """
    Renames aspect classes across all target files.
    Returns dict mapping file path to col_counts dict.
    """
    patterns = build_replacement_patterns(renames)
    results = {}

    for file_path, target_columns in TARGET_SPECS:
        rel_path = os.path.relpath(file_path, REPO_ROOT)
        col_counts = process_file(file_path, target_columns, patterns, dry_run=dry_run)
        results[rel_path] = col_counts

    return results


def parse_mapping_file(mapping_path: str) -> Dict[str, str]:
    """
    Loads mapping dictionary from JSON or CSV file.
    CSV format expected: old_name,new_name or old_class,new_class
    """
    renames = {}
    if mapping_path.endswith(".json"):
        with open(mapping_path, "r", encoding="utf-8") as f:
            renames = json.load(f)
    elif mapping_path.endswith(".csv"):
        with open(mapping_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            # If first row has header like old_class,new_class
            for row in reader:
                if len(row) >= 2:
                    renames[row[0].strip()] = row[1].strip()
    else:
        raise ValueError("Mapping file must be .json or .csv")
    return renames


def main():
    parser = argparse.ArgumentParser(
        description="Rename aspect classes across data and curated files."
    )
    parser.add_argument("--old", type=str, help="Old aspect class name to replace")
    parser.add_argument("--new", type=str, help="New aspect class name")
    parser.add_argument(
        "--mapping",
        type=str,
        help="Path to JSON or CSV file mapping old names to new names",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Preview changes without modifying files"
    )

    args = parser.parse_args()

    renames = {}
    if args.mapping:
        renames = parse_mapping_file(args.mapping)
    elif args.old and args.new:
        renames = {args.old.strip(): args.new.strip()}
    else:
        parser.error("Must specify either --old and --new, or --mapping")

    if not renames:
        print("No valid renames specified.")
        sys.exit(0)

    mode_str = " (DRY RUN)" if args.dry_run else ""
    print(f"--- Renaming Aspect Classes{mode_str} ---")
    for old_name, new_name in renames.items():
        print(f"  '{old_name}' -> '{new_name}'")
    print()

    results = rename_aspect_classes(renames, dry_run=args.dry_run)

    total_replacements = 0
    for rel_path, col_counts in results.items():
        subtotal = sum(col_counts.values())
        total_replacements += subtotal
        col_str = ", ".join([f"{col}: {cnt}" for col, cnt in col_counts.items()])
        print(f"{rel_path:<50} -> Total: {subtotal} ({col_str})")

    print(f"\nTotal replacements across all files: {total_replacements}")


if __name__ == "__main__":
    main()
