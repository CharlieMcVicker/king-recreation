import json
import os
import argparse
import csv
from collections import defaultdict, Counter
from typing import Optional, List, Dict, Any

from king_recreation.pattern_registry import PatternRegistry


def load_csv(path: str) -> List[Dict[str, str]]:
    with open(path, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(path: str, data: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with open(path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def save_json(path: str, data: Any) -> None:
    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def load_json(path: str) -> Any:
    with open(path, mode="r", encoding="utf-8") as f:
        return json.load(f)


def analyze_matches(classes_path: Optional[str] = None):
    matches_path = "artifacts/data/matches_initial.csv"
    corpus_path = "artifacts/data/corpus.csv"

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
    pattern_registry = PatternRegistry.get_instance()
    pattern_registry.load_from_csv(classes_path)

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
        row["scope"] = "ending"
        key = (
            corpus_id if corpus_id else verb,
            cls,
        )

        if key not in filtered_matches:
            filtered_matches[key] = row

    # Integrate Reconstructs (validated matches)
    validated_matches_path = "artifacts/data/matches_validated.csv"
    if os.path.exists(validated_matches_path):
        validated_matches = load_csv(validated_matches_path)
        for row in validated_matches:
            verb = row["definition"]
            corpus_id = row.get("corpus_id", "")
            cls = row["class"]
            row["scope"] = "reconstructs"
            key = (corpus_id if corpus_id else verb, cls)

            # Insert or upgrade
            filtered_matches[key] = row

    class_counts = defaultdict((lambda: defaultdict(int)))
    for row in filtered_matches.values():
        class_counts[row["class"].split("[")[0]][row["scope"]] += 1

    class_match_data = []
    for macro in pattern_registry.macros:
        class_match_data.append(
            {
                "class": macro.name,
                "ending": class_counts[macro.name]["ending"],
                "reconstructs": class_counts[macro.name]["reconstructs"],
            }
        )

    output_dir = "artifacts/reports"
    os.makedirs(output_dir, exist_ok=True)

    save_csv(
        os.path.join(output_dir, "class_match_counts.csv"),
        class_match_data,
        ["class", "ending", "reconstructs"],
    )

    # 2. Verb Coverage Summary
    coverage_summary = {}

    for scope_target in ["reconstructs", "ending"]:
        verb_match_counts = defaultdict(int)
        for key, row in filtered_matches.items():
            id_val, cls = key

            # Range matching: scope_target defines the MINIMUM level
            # reconstructs tier
            if scope_target == "reconstructs":
                if row["scope"] == "reconstructs":
                    verb_match_counts[id_val] += 1

            # ending tier includes anything
            else:
                if row["scope"] in ["ending", "reconstructs"]:
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

        coverage_summary[scope_target] = {
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

    target_set = set(verb for verb, _ in filtered_matches)

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
    unmatched_data.sort(key=lambda x: (x.get("perfective", "")[::-1], x["corpus_id"]))

    save_csv(
        os.path.join(output_dir, f"unmatched_verbs.csv"),
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

    print(f"Analysis complete. Artifacts generated in {output_dir}/")

    # 4. Root Ambiguity Analysis
    reconstructable_path = "artifacts/data/reconstructable_verbs.json"
    if os.path.exists(reconstructable_path):
        reconstructable_verbs = load_json(reconstructable_path)

        # fun little check - do any verbs have matching h-grade roots but not glottal-grade roots?
        glottal_grades_by_h_grade = defaultdict(set)
        for verb in reconstructable_verbs:
            h_grade = verb.get("h_grade_root")
            glottal_grade = verb.get("glottal_grade_root")
            glottal_grades_by_h_grade[h_grade].add(glottal_grade)

        distinct_non_null_g_grades = {
            k: v
            for k, v in glottal_grades_by_h_grade.items()
            if len([v1 for v1 in v if v1]) > 1
        }

        print("[INFO]", distinct_non_null_g_grades)

        # Group corpus_ids by h_grade_root then glottal_grade
        root_groups = defaultdict(lambda: defaultdict(set))
        for verb in reconstructable_verbs:
            h_grade = verb.get("h_grade_root")
            glottal_grade = verb.get("glottal_grade_root")
            corpus_id = verb.get("corpus_id")

            root_groups[h_grade][glottal_grade].add(corpus_id)

        # In the case that exactly one glottal grade root is attested
        # combine verbs with unattested glottal grade into same grouping

        for h_grade in root_groups:
            if None in root_groups[h_grade] and len(root_groups[h_grade]) == 2:
                attested_root = next(x for x in root_groups[h_grade] if x is not None)
                root_groups[h_grade] = {
                    attested_root: root_groups[h_grade][attested_root].union(
                        root_groups[h_grade][None]
                    )
                }

        # Count unique corpus IDs for each root pair and export raw data
        root_ambiguity_data = []
        for h_grade in root_groups:
            for g_grade, corpus_ids in root_groups[h_grade].items():
                root_ambiguity_data.append(
                    {
                        "h_grade": h_grade if h_grade is not None else "",
                        "g_grade": g_grade if g_grade is not None else "",
                        "count": len(corpus_ids),
                    }
                )

        # Sort for stability: count desc, then h_grade
        root_ambiguity_data.sort(key=lambda x: (-x["count"], x["h_grade"]))

        save_csv(
            os.path.join(output_dir, "root_ambiguity_counts.csv"),
            root_ambiguity_data,
            ["h_grade", "g_grade", "count"],
        )

        print(
            f"Root ambiguity counts saved to {os.path.join(output_dir, 'root_ambiguity_counts.csv')}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze match data.")
    parser.add_argument("--visualize", action="store_true", help="Run visualization.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()

    analyze_matches(args.classes)

    if args.visualize:
        from king_recreation.visualize_analysis import run_all_visualizations

        run_all_visualizations()
