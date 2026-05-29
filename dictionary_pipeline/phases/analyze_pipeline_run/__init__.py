import argparse
import os
import re
from collections import Counter, defaultdict
from typing import Any

import pandas as pd

from dictionary_pipeline.paths import (
    CLASS_ENDING_PROFILES_CSV_PATH,
    VALIDATED_MATCHES_PATH,
)
from dictionary_pipeline.phases.analyze_pipeline_run.artifacts import (
    save_class_match_counts,
    save_furthest_corpus_by_id,
    save_macro_variant_data,
    save_root_ambiguity_counts,
    save_root_macro_distribution,
    save_unmatched_verbs,
    save_unused_variants,
    save_variant_match_counts,
    save_variation_match_counts,
    save_verb_coverage,
)
from dictionary_pipeline.phases.identify_aspect_classes.artifacts import (
    load_matches as load_raw_matches,
)
from dictionary_pipeline.phases.identify_aspect_classes.artifacts import (
    load_stripped_corpus as load_corpus_no_asp,
)
from dictionary_pipeline.phases.identify_prefixes.artifacts import (
    load_stripped_roots as load_corpus_no_pre,
)
from dictionary_pipeline.phases.preprocess_ced.artifacts import load_corpus
from dictionary_pipeline.phases.reconstruct_and_validate.artifacts import (
    load_validated_matches,
)
from dictionary_pipeline.phases.reconstruct_and_validate.artifacts import (
    load_validated_roots as load_validated_reconstructable_roots,
)
from dictionary_pipeline.phases.select_canonical_derivations.artifacts import (
    load_reconstructable_verbs,
)
from dictionary_pipeline.row_models import ProcessedRow
from morphology.morphemes.aspect.pattern_registry import PatternRegistry


def _prepare_filtered_matches(
    matches: list[dict[str, Any]], validated_matches_path: str
) -> dict[tuple[Any, ...], dict[str, Any]]:
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

    validated_matches = load_validated_matches()
    for row in validated_matches:
        verb = row["definition"]
        corpus_id = row.get("corpus_id", "")
        cls = row["class"]
        row["scope"] = "reconstructs"
        key = (corpus_id if corpus_id else verb, cls)
        filtered_matches[key] = row
    return filtered_matches


def _analyze_class_matches(
    filtered_matches: dict[tuple[Any, ...], dict[str, Any]],
    pattern_registry: PatternRegistry,
) -> list[dict[str, Any]]:
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
    filtered_matches: dict[tuple[Any, ...], dict[str, Any]], all_verbs: set[str]
) -> dict[str, Any]:
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
    filtered_matches: dict[tuple[Any, ...], dict[str, Any]],
    all_verbs: set[str],
    corpus: list[ProcessedRow],
) -> list[dict[str, Any]]:
    verb_forms_map = {row.meta.corpus_id: row for row in corpus}
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
            data["definition"] = verb_forms_map[v].meta.definition
            for field in form_fields[1:]:
                data[field] = getattr(verb_forms_map[v].forms, field, "")
        unmatched_data.append(data)

    unmatched_data.sort(key=lambda x: (x.get("perfective", "")[::-1], x["corpus_id"]))
    return unmatched_data


def _analyze_root_ambiguity() -> list[dict[str, Any]]:
    reconstructable_verbs = load_reconstructable_verbs()
    if reconstructable_verbs is None:
        return []

    # Group corpus_ids by h_grade_root then glottal_grade
    root_groups = defaultdict(lambda: defaultdict(set))
    for verb in reconstructable_verbs:
        h_grade = verb.morphology.h_grade_root
        glottal_grade = verb.morphology.glottal_grade_root
        corpus_id = verb.corpus_id
        root_groups[h_grade][glottal_grade].add(corpus_id)

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


def _analyze_macro_variants(pattern_registry: PatternRegistry) -> dict[str, Any]:
    reconstructable_verbs = load_reconstructable_verbs()
    if reconstructable_verbs is None:
        return {}
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
        class_name = verb.morphology.class_name or ""
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

    # Identify unused options and calculate statistics
    for macro_name, data in analysis.items():
        unused = []
        for slot, count in data["available_options"].items():
            for i in range(1, count + 1):
                if data["slots"][slot][i] == 0:
                    unused.append(f"{slot}{i}" if i > 1 else f"{slot}(base)")
        data["unused_options"] = unused

        # Calculate variant statistics
        data["variant_stats"] = []
        total_matches = data["total_matches"]
        can_have_variants = any(
            count > 1 for count in data["available_options"].values()
        )
        data["can_have_variants"] = can_have_variants

        if total_matches > 0:
            for variant, count in data["combinations"].items():
                data["variant_stats"].append(
                    {
                        "variant": variant,
                        "count": count,
                        "percent": round(count / total_matches * 100, 2),
                    }
                )

    return analysis


def _identify_dead_variants(macro_variant_data: dict[str, Any]) -> list[dict[str, Any]]:
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


def _save_variant_match_csv(macro_variant_data: dict[str, Any]) -> None:
    flattened_data = []
    for macro_name, data in macro_variant_data.items():
        if "variant_stats" in data:
            if data.get("can_have_variants", False):
                for stat in data["variant_stats"]:
                    flattened_data.append(
                        {
                            "macro_class": macro_name,
                            "variant_name": stat["variant"],
                            "match_count": stat["count"],
                            "match_percent": stat["percent"],
                            "can_have_variants": True,
                        }
                    )

    # Sort by match count descending, then macro class
    flattened_data.sort(key=lambda x: (-x["match_count"], x["macro_class"]))

    save_variant_match_counts(
        flattened_data,
        [
            "macro_class",
            "variant_name",
            "match_count",
            "match_percent",
            "can_have_variants",
        ],
    )


def _save_variation_match_csv(macro_variant_data: dict[str, Any]) -> None:
    flattened_data = []
    for macro_name, data in macro_variant_data.items():
        if data.get("can_have_variants", False) and "slots" in data:
            total_matches = data["total_matches"]
            available_options = data.get("available_options", {})
            for slot, counts in data["slots"].items():
                # Only include slots with more than one variation (i.e., in competition)
                if available_options.get(slot, 0) <= 1:
                    continue

                for idx, count in counts.items():
                    if count > 0:
                        variation_name = f"{slot}{idx}" if idx > 1 else f"{slot}(base)"
                        percent = (
                            round(count / total_matches * 100, 2)
                            if total_matches > 0
                            else 0
                        )
                        flattened_data.append(
                            {
                                "macro_class": macro_name,
                                "variation_name": variation_name,
                                "match_count": count,
                                "match_percent": percent,
                                "can_have_variants": True,
                            }
                        )

    # Sort by match count descending, then macro class
    flattened_data.sort(key=lambda x: (-x["match_count"], x["macro_class"]))

    save_variation_match_counts(
        flattened_data,
        [
            "macro_class",
            "variation_name",
            "match_count",
            "match_percent",
            "can_have_variants",
        ],
    )


def _analyze_ending_profiles(profiles_path: str) -> None:
    """
    Analyzes the distribution of surface sequences and their match percentages.
    """
    if not os.path.exists(profiles_path):
        return

    df = pd.read_csv(profiles_path)
    if df.empty:
        return

    # 1. Sequences per class
    sequence_counts = df.groupby("class").size()
    avg_seq_per_class = sequence_counts.mean()
    max_seq_per_class = sequence_counts.max()

    # 2. Percentage distribution
    class_totals = df.groupby("class")["count"].transform("sum")
    df["percentage"] = (df["count"] / class_totals) * 100

    # print("\nEnding Profile Distribution Summary:")
    # print(f"Total Unique Profiles: {len(df)}")
    # print(f"Average Unique Sequences per Class: {avg_seq_per_class:.2f}")
    # print(f"Max Unique Sequences in a Class: {max_seq_per_class}")

    # print("\nTop Classes by Unique Sequences:")
    # top_classes = sequence_counts.sort_values(ascending=False).head(5)
    # for cls, count in top_classes.items():
    #     print(f"  {cls:<20}: {count}")

    # print("\nSequence Percentage Buckets:")
    # # Use pandas cut to see distribution
    # bins = [0, 20, 40, 60, 80, 100]
    # buckets = pd.cut(df["percentage"], bins=bins).value_counts().sort_index()
    # for interval, count in buckets.items():
    #     print(f"  {str(interval):<15}: {count} sequences")


def _analyze_roots_by_macro(registry: PatternRegistry) -> None:
    data = load_reconstructable_verbs()
    if data is None:
        return

    classes_to_parents = {
        pattern.name: parent
        for parent in registry.macros_by_parent
        for pattern in registry.macros_by_parent[parent]
    }

    final_letters_by_class = defaultdict(set)

    for entry in data:
        class_name = entry.morphology.class_name.split("[")[0]
        h_grade_root = entry.morphology.h_grade_root
        key = (
            classes_to_parents[class_name],
            class_name,
        )

        if class_name and h_grade_root:
            # Get the last character of the h_grade_root
            final_letter = h_grade_root[-1]
            final_letters_by_class[key].add(final_letter)

    # Convert sets to sorted lists for JSON serialization and easier diffing
    vowels = {"a", "e", "i", "o", "u", "v"}
    rows = [
        {
            "parent": parent,
            "class": class_name,
            "letters": ";".join(sorted(list(letters))),
            "only_vowels": all(l in vowels for l in letters),
            "only_laryngeal": all(l in {"h", "'"} for l in letters),
            "only_consonants": all(l not in vowels for l in letters),
        }
        for (parent, class_name), letters in sorted(final_letters_by_class.items())
    ]

    save_root_macro_distribution(
        rows,
        fieldnames=[
            "parent",
            "class",
            "only_vowels",
            "only_consonants",
            "only_laryngeal",
            "letters",
        ],
    )


def _analyze_verb_status() -> None:
    corpus_data = load_corpus()
    no_asp_keys = set(
        (row.get("corpus_id"), row.get("prediction"))
        for row in load_corpus_no_asp()
        if row.get("corpus_id") and row.get("prediction")
    )
    no_pre_keys = set(
        (row.get("corpus_id"), row.get("prediction"))
        for row in load_corpus_no_pre()
        if row.get("corpus_id") and row.get("prediction")
    )
    validated_keys = set(
        (row.get("corpus_id"), row.get("prediction"))
        for row in load_validated_reconstructable_roots()
        if row.get("corpus_id") and row.get("prediction")
    )

    best_by_id = []
    for row in corpus_data:
        id = row.meta.corpus_id
        pred = row.meta.prediction.value
        key = (id, pred)
        best = "0.corpus"
        if key in no_asp_keys:
            best = "1.asp_stripped"
        if key in no_pre_keys:
            best = "2.pre_stripped"
        if key in validated_keys:
            best = "3.validated"

        best_by_id.append(
            {
                "corpus_id": id,
                "prediction": pred,
                "definition": row.meta.definition,
                "furthest_corpus": best,
            }
        )

    save_furthest_corpus_by_id(
        sorted(
            best_by_id,
            key=lambda x: (
                x["furthest_corpus"][0],
                x["corpus_id"],
                x["prediction"],
            ),
        ),
        ["corpus_id", "prediction", "definition", "furthest_corpus"],
    )


def analyze_pipeline_run(classes_path: str | None = None) -> None:
    """
    Analyze the results of the pipeline and generate summary statistics.

    Inputs:
    * MATCHES_PATH: Raw aspect class matches.
    * CORPUS_PATH: Original corpus.
    * RECONSTRUCTABLE_VERBS_PATH: Final reconstructed verbs.
    * VALIDATED_MATCHES_PATH: Validated matches.

    Outputs:
    * CLASS_MATCH_COUNTS_PATH: Counts of matches per class.
    * VERB_COVERAGE_PATH: JSON summary of verb coverage.
    * UNMATCHED_VERBS_PATH: List of verbs not matched/reconstructed.
    * ROOT_AMBIGUITY_COUNTS_PATH: Statistics on root ambiguity.
    * MACRO_VARIANT_DATA_PATH: Analysis of macro-class variants.
    """

    matches = load_raw_matches()
    corpus = load_corpus()
    if not matches or not corpus:
        print("Required inputs missing.")
        return

    pattern_registry = PatternRegistry.get_instance()
    pattern_registry.load_from_csv(classes_path)

    all_verbs: set[str] = set(
        row.meta.corpus_id if row.meta.corpus_id else row.meta.definition
        for row in corpus
    )
    total_verb_count = len(all_verbs)

    # 2. Perform Analysis Steps
    filtered_matches = _prepare_filtered_matches(matches, VALIDATED_MATCHES_PATH)
    class_match_data = _analyze_class_matches(filtered_matches, pattern_registry)
    coverage_summary = _analyze_verb_coverage(filtered_matches, all_verbs)
    unmatched_verbs_data = _get_unmatched_verbs(filtered_matches, all_verbs, corpus)
    root_ambiguity_data = _analyze_root_ambiguity()
    macro_variant_data = _analyze_macro_variants(pattern_registry)
    unused_variants_report = _identify_dead_variants(macro_variant_data)
    _analyze_roots_by_macro(registry=pattern_registry)
    _analyze_ending_profiles(CLASS_ENDING_PROFILES_CSV_PATH)

    # 3. Output Data to Disk
    _analyze_verb_status()

    save_class_match_counts(
        class_match_data,
        ["class", "ending", "reconstructs"],
    )

    save_verb_coverage(coverage_summary)

    form_fields = [
        "definition",
        "present",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    save_unmatched_verbs(
        unmatched_verbs_data,
        ["corpus_id"] + form_fields,
    )

    if root_ambiguity_data:
        save_root_ambiguity_counts(
            root_ambiguity_data,
            ["h_grade", "g_grade", "count"],
        )

    if macro_variant_data:
        save_macro_variant_data(macro_variant_data)
        _save_variant_match_csv(macro_variant_data)
        _save_variation_match_csv(macro_variant_data)

    if unused_variants_report is not None:
        save_unused_variants(unused_variants_report)

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

    print(f"Analysis complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze match data.")
    parser.add_argument("--visualize", action="store_true", help="Run visualization.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()

    analyze_pipeline_run(args.classes)

    if args.visualize:
        from dictionary_pipeline.phases.visualize_analysis import visualize_all

        visualize_all()
