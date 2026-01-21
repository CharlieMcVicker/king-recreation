import json
import os
import argparse
import csv
from collections import defaultdict, Counter
from typing import Optional, List, Dict, Any

import re
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


def _prepare_filtered_matches(
    matches: List[Dict[str, Any]], validated_matches_path: str
) -> Dict[tuple, Dict[str, Any]]:
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

    if os.path.exists(validated_matches_path):
        validated_matches = load_csv(validated_matches_path)
        for row in validated_matches:
            verb = row["definition"]
            corpus_id = row.get("corpus_id", "")
            cls = row["class"]
            row["scope"] = "reconstructs"
            key = (corpus_id if corpus_id else verb, cls)
            filtered_matches[key] = row
    return filtered_matches


def _analyze_class_matches(
    filtered_matches: Dict[tuple, Dict[str, Any]], pattern_registry: PatternRegistry
) -> List[Dict[str, Any]]:
    class_counts = defaultdict(lambda: defaultdict(int))
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
    return class_match_data


def _analyze_verb_coverage(
    filtered_matches: Dict[tuple, Dict[str, Any]], all_verbs: set
) -> Dict[str, Any]:
    total_verb_count = len(all_verbs)
    coverage_summary = {}

    for scope_target in ["reconstructs", "ending"]:
        verb_match_counts = defaultdict(int)
        for key, row in filtered_matches.items():
            id_val, _ = key

            if scope_target == "reconstructs":
                if row["scope"] == "reconstructs":
                    verb_match_counts[id_val] += 1
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
    return coverage_summary


def _get_unmatched_verbs(
    filtered_matches: Dict[tuple, Dict[str, Any]],
    all_verbs: set,
    corpus: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
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
        data = {"corpus_id": v}
        if v in verb_forms_map:
            for field in form_fields:
                data[field] = verb_forms_map[v].get(field, "")
        unmatched_data.append(data)

    unmatched_data.sort(key=lambda x: (x.get("perfective", "")[::-1], x["corpus_id"]))
    return unmatched_data


def _analyze_root_ambiguity(reconstructable_path: str) -> List[Dict[str, Any]]:
    if not os.path.exists(reconstructable_path):
        return []

    reconstructable_verbs = load_json(reconstructable_path)

    # h-grade vs glottal-grade check
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
    if distinct_non_null_g_grades:
        print("[INFO]", distinct_non_null_g_grades)

    # Group corpus_ids by h_grade_root then glottal_grade
    root_groups = defaultdict(lambda: defaultdict(set))
    for verb in reconstructable_verbs:
        h_grade = verb.get("h_grade_root")
        glottal_grade = verb.get("glottal_grade_root")
        corpus_id = verb.get("corpus_id")
        root_groups[h_grade][glottal_grade].add(corpus_id)

    # Combine unattested glottal grades if only one attested exists
    for h_grade in root_groups:
        if None in root_groups[h_grade] and len(root_groups[h_grade]) == 2:
            attested_root = next(x for x in root_groups[h_grade] if x is not None)
            root_groups[h_grade] = {
                attested_root: root_groups[h_grade][attested_root].union(
                    root_groups[h_grade][None]
                )
            }

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

    root_ambiguity_data.sort(key=lambda x: (-x["count"], x["h_grade"]))
    return root_ambiguity_data


def _analyze_macro_variants(
    reconstructable_path: str, pattern_registry: PatternRegistry
) -> Dict[str, Any]:
    if not os.path.exists(reconstructable_path):
        return {}

    reconstructable_verbs = load_json(reconstructable_path)
    # pattern captures the base name and then the digits for each form if present
    # eg. v'vsk[perf2-inf2] -> ("v'vsk", None, None, "2", None, "2")
    pattern_regex = r"([\w\-'\*]+)(?:\[(?:pres(\d+))?\-?(?:imperf(\d+))?\-?(?:perf(\d+))?\-?(?:imp(\d+))?\-?(?:inf(\d+))?\])?"

    # macro_name -> { "combinations": Counter(full_name), "slots": { "perf": { 1: count, 2: count } } }
    analysis = {}
    for macro in pattern_registry.macros:
        analysis[macro.name] = {
            "combinations": Counter(),
            "slots": {
                "pres": Counter(),
                "imperf": Counter(),
                "perf": Counter(),
                "imp": Counter(),
                "inf": Counter(),
            },
            "total_matches": 0,
            "available_options": {
                "pres": len(macro.present),
                "imperf": len(macro.imperfective),
                "perf": len(macro.perfective),
                "imp": len(macro.imperative),
                "inf": len(macro.infinitive),
            },
        }

    for verb in reconstructable_verbs:
        class_name = verb.get("class_name", "")
        match = re.match(pattern_regex, class_name)
        if not match:
            continue

        base_name = match.group(1)
        if base_name not in analysis:
            continue

        analysis[base_name]["combinations"][class_name] += 1
        analysis[base_name]["total_matches"] += 1

        # Extract indices (match groups 2-6)
        # indices are 1-based. if matched group is None, it's 1.
        slots = ["pres", "imperf", "perf", "imp", "inf"]
        for i, slot in enumerate(slots):
            idx = int(match.group(i + 2) or 1)
            analysis[base_name]["slots"][slot][idx] += 1

    # Identify unused options
    for macro_name, data in analysis.items():
        unused = []
        for slot, count in data["available_options"].items():
            for i in range(1, count + 1):
                if data["slots"][slot][i] == 0:
                    unused.append(f"{slot}{i}" if i > 1 else f"{slot}(base)")
        data["unused_options"] = unused

    return analysis


def _identify_dead_variants(macro_variant_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Summarizes which variants of which macros are never used across the entire corpus.
    """
    dead_variants = []
    for macro_name, data in macro_variant_data.items():
        if data.get("unused_options"):
            dead_variants.append(
                {
                    "macro": macro_name,
                    "total_matches": data["total_matches"],
                    "unused_variants": data["unused_options"],
                }
            )

    # Sort by total matches (descending) then macro name
    dead_variants.sort(key=lambda x: (-x["total_matches"], x["macro"]))
    return dead_variants


def analyze_matches(classes_path: Optional[str] = None):
    matches_path = "artifacts/data/matches_initial.csv"
    corpus_path = "artifacts/data/corpus.csv"
    validated_matches_path = "artifacts/data/matches_validated.csv"
    reconstructable_path = "artifacts/data/reconstructable_verbs.json"
    output_dir = "artifacts/reports"

    # 1. Validation and Setup
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

    # 2. Perform Analysis Steps
    filtered_matches = _prepare_filtered_matches(matches, validated_matches_path)
    class_match_data = _analyze_class_matches(filtered_matches, pattern_registry)
    coverage_summary = _analyze_verb_coverage(filtered_matches, all_verbs)
    unmatched_verbs_data = _get_unmatched_verbs(filtered_matches, all_verbs, corpus)
    root_ambiguity_data = _analyze_root_ambiguity(reconstructable_path)
    macro_variant_data = _analyze_macro_variants(reconstructable_path, pattern_registry)
    unused_variants_report = _identify_dead_variants(macro_variant_data)

    # 3. Output Data to Disk
    os.makedirs(output_dir, exist_ok=True)

    save_csv(
        os.path.join(output_dir, "class_match_counts.csv"),
        class_match_data,
        ["class", "ending", "reconstructs"],
    )

    save_json(os.path.join(output_dir, "verb_coverage.json"), coverage_summary)

    form_fields = [
        "definition",
        "present",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    save_csv(
        os.path.join(output_dir, "unmatched_verbs.csv"),
        unmatched_verbs_data,
        ["corpus_id"] + form_fields,
    )

    if root_ambiguity_data:
        save_csv(
            os.path.join(output_dir, "root_ambiguity_counts.csv"),
            root_ambiguity_data,
            ["h_grade", "g_grade", "count"],
        )

    if macro_variant_data:
        save_json(
            os.path.join(output_dir, "macro_variant_data.json"), macro_variant_data
        )

    if unused_variants_report is not None:
        save_json(
            os.path.join(output_dir, "unused_variants.json"), unused_variants_report
        )

    # 4. Console Summary
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
    if root_ambiguity_data:
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
