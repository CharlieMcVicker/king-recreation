from king_recreation.pattern_registry import PatternRegistry
from typing import Optional
import csv
import json
import os
import argparse
from collections import defaultdict


def load_csv(path):
    with open(path, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(path, data, fieldnames):
    with open(path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def save_json(path, data):
    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def analyze_matches(classes_path: Optional[str] = None):
    matches_path = "artifacts/data/matches_initial.csv"
    corpus_path = "artifacts/data/corpus.csv"
    stem_corpus_path = "artifacts/data/derived_roots.csv"

    if not os.path.exists(matches_path):
        print(f"Error: {matches_path} not found.")
        return
    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        return
    if classes_path and not os.path.exists(classes_path):
        print(f"Error: {classes_path} not found.")
        return

    matches = load_csv(matches_path)
    corpus = load_csv(corpus_path)
    stem_corpus = load_csv(stem_corpus_path) if os.path.exists(stem_corpus_path) else []
    pattern_registry = PatternRegistry.get_instance()
    pattern_registry.load_from_csv(classes_path)

    stem_corpus_map = {
        (row["corpus_id"] if "corpus_id" in row else row["definition"]): row
        for row in stem_corpus
    }

    all_verbs = set(
        row["corpus_id"] if "corpus_id" in row else row["definition"] for row in corpus
    )
    total_verb_count = len(all_verbs)

    # 1. Class-wise Match Counts
    filtered_matches = {}
    for row in matches:
        verb = row["definition"]
        corpus_id = row.get("corpus_id", "")
        cls = row["class"]
        strictness = row["strictness"]
        scope = row["scope"]
        key = (corpus_id if corpus_id else verb, cls, strictness)

        if key not in filtered_matches:
            filtered_matches[key] = row
        else:
            # Upgrade scope if better match found (reconstructs > full > ending)
            # Ranking: reconstructs=3, full=2, ending=1
            rank = {"reconstructs": 3, "full": 2, "ending": 1}
            current_scope = filtered_matches[key]["scope"]
            if rank.get(scope, 0) > rank.get(current_scope, 0):
                filtered_matches[key] = row

    # Integrate Reconstructs (validated matches)
    validated_matches_path = "artifacts/data/matches_validated.csv"
    if os.path.exists(validated_matches_path):
        validated_matches = load_csv(validated_matches_path)
        for row in validated_matches:
            verb = row["definition"]
            corpus_id = row.get("corpus_id", "")
            cls = row["class"]
            strictness = row["strictness"]
            scope = row["scope"]  # Should be 'reconstructs'
            key = (corpus_id if corpus_id else verb, cls, strictness)

            # Insert or upgrade
            filtered_matches[key] = row
            # If we have a validated match, it implies full match + reconstruction success.
            # We might need to ensure stem_final_match columns exist if we're overwriting a "matches.csv" row
            # But the 'matches_validated.csv' usually doesn't have stem_final details.
            # However, for the purpose of coverage stats (scope), this is sufficient.
            # If we need stem_final details for near-miss analysis, we might technically lose them if we overwrite completely
            # but usually a 'reconstructs' match was already a 'full' match in matches.csv, so we just want to promote the scope.
            # Let's try to preserve other fields if updating an existing key.
            # Actually, `matches_validated.csv` only has [definition,class,strictness,scope].
            # If we just overwrite, we lose `stem_final_match_*`.
            # We should UPDATE the existing entry if present, or create new.

            # Since 'reconstructs' implies it was already found as a match (usually),
            # let's check if it exists in filtered_matches (from matches.csv)
            if key in filtered_matches:
                filtered_matches[key]["scope"] = scope
            else:
                # If it wasn't in matches.csv (maybe a manual addition? or custom pipeline?), add it.
                # We'll validly lack the stem_final columns, but that's okay for coverage counts.
                filtered_matches[key] = row

    class_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for row in filtered_matches.values():
        class_counts[row["class"].split("[")[0]][row["strictness"]][row["scope"]] += 1

    class_match_data = []
    for macro in pattern_registry.macros:
        class_match_data.append(
            {
                "class": macro.name,
                "strict_ending": class_counts[macro.name]["strict"]["ending"],
                "strict_full": class_counts[macro.name]["strict"]["full"],
                "strict_reconstructs": class_counts[macro.name]["strict"][
                    "reconstructs"
                ],
                "loose_ending": class_counts[macro.name]["loose"]["ending"],
                "loose_full": class_counts[macro.name]["loose"]["full"],
            }
        )

    output_dir = "artifacts/reports"
    os.makedirs(output_dir, exist_ok=True)

    save_csv(
        os.path.join(output_dir, "class_match_counts.csv"),
        class_match_data,
        [
            "class",
            "strict_ending",
            "strict_full",
            "strict_reconstructs",
            "loose_ending",
            "loose_full",
        ],
    )

    # 2. Verb Coverage Summary
    coverage_summary = {}
    combos = [
        ("strict", "reconstructs"),
        ("strict", "full"),
        ("loose", "full"),
        ("strict", "ending"),
        ("loose", "ending"),
    ]

    for strictness, scope_target in combos:
        verb_match_counts = defaultdict(int)
        for key, row in filtered_matches.items():
            id_val, cls, s = key
            if s == strictness:
                # Range matching: scope_target defines the MINIMUM level
                # reconstructs tier
                if scope_target == "reconstructs":
                    if row["scope"] == "reconstructs":
                        verb_match_counts[id_val] += 1
                # full tier includes reconstructs
                elif scope_target == "full":
                    if row["scope"] in ["full", "reconstructs"]:
                        verb_match_counts[id_val] += 1
                # ending tier includes all
                else:
                    if row["scope"] in ["ending", "full", "reconstructs"]:
                        verb_match_counts[id_val] += 1

        matched_verbs = set(verb_match_counts.keys())
        zero = len(all_verbs - matched_verbs)
        one = 0
        multiple = 0
        for count in verb_match_counts.values():
            if count == 1:
                one += 1
            elif count > 1:
                multiple += 1

        coverage_summary[f"{strictness}_{scope_target}"] = {
            "0": zero,
            "1": one,
            "2+": multiple,
            "coverage_pct": (
                round((total_verb_count - zero) / total_verb_count * 100, 1)
                if total_verb_count > 0
                else 0.0
            ),
        }

    save_json(os.path.join(output_dir, "verb_coverage.json"), coverage_summary)

    # 2b. Export Unmatched Verbs
    verb_forms_map = {row["corpus_id"]: row for row in corpus}
    form_fields = [
        "definition",
        "present",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]

    for strictness in ["strict", "loose"]:
        target_set = set()
        for key, row in filtered_matches.items():
            verb, cls, s = key
            # Unmatched here means "no full match" (or better)
            if s == strictness and row["scope"] in ["full", "reconstructs"]:
                target_set.add(verb)

        unmatched = list(all_verbs - target_set)
        unmatched_data = []
        for v in unmatched:
            data = {
                "corpus_id": v,
            }
            if v in verb_forms_map:
                for field in form_fields:
                    data[field] = verb_forms_map[v].get(field, "")
            unmatched_data.append(data)

        # Sort by reversed perfective string to group by ending, then by verb for stability
        unmatched_data.sort(
            key=lambda x: (x.get("perfective", "")[::-1], x["corpus_id"])
        )

        save_csv(
            os.path.join(output_dir, f"unmatched_verbs_{strictness}.csv"),
            unmatched_data,
            ["corpus_id"] + form_fields,
        )

    # Print summary to console
    print("\nVerb Class Coverage Summary:")
    print(f"{'Match Configuration':<20} | {'Count (>=1)':<12} | {'Percentage':<10}")
    print("-" * 48)
    for key in sorted(
        coverage_summary.keys(),
        key=lambda x: (0 if "reconstructs" in x else (1 if "full" in x else 2), x),
    ):
        stats = coverage_summary[key]
        matched = total_verb_count - stats["0"]
        pct = stats["coverage_pct"]
        print(f"{key:<20} | {matched:<12} | {pct:>9}%")
    print("")

    # 3. Class Near-Miss Analysis
    near_miss_data = []
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]

    near_miss_groups = defaultdict(list)
    for row in filtered_matches.values():
        if row["scope"] == "ending":
            near_miss_groups[(row["class"], row["strictness"])].append(row)

    for macro in pattern_registry.macros:
        for s in ["strict", "loose"]:
            group = near_miss_groups[(macro.name, s)]
            match_count = len(group)
            rates = {}
            for form in forms:
                if match_count > 0:
                    col = f"stem_final_match_{form}"
                    passed = sum(1 for r in group if r[col].lower() == "true")
                    rate = round(passed / match_count, 3)
                else:
                    rate = 0.0
                rates[f"{form}_rate"] = rate

            data_row = {
                "class": macro.name,
                "strictness": s,
                "match_count": match_count,
                **rates,
            }
            near_miss_data.append(data_row)

    near_miss_data.sort(
        key=lambda x: (
            (pattern_registry.key_for_pattern_name(x["class"])),
            x["strictness"],
        )
    )

    save_csv(
        os.path.join(output_dir, "class_near_misses.csv"),
        near_miss_data,
        ["class", "strictness", "match_count"] + [f"{f}_rate" for f in forms],
    )

    print(f"Analysis complete. Artifacts generated in {output_dir}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze match data.")
    parser.add_argument("--visualize", action="store_true", help="Run visualization.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()

    analyze_matches(args.classes)

    if args.visualize:
        from king_recreation.visualize_analysis import run_all_visualizations

        run_all_visualizations()
