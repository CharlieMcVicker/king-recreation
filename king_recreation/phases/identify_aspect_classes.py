import csv
import os
from collections import defaultdict
from typing import List

from king_recreation.morphemes.aspect.class_patterns import (
    ExpandedClassPattern,
    StrippedVerbRow,
)
from king_recreation.morphemes.aspect.pattern_registry import PatternRegistry
from king_recreation.paths import CORPUS_NO_ASP_PATH, CORPUS_PATH, MATCHES_PATH


def group_matches_by_macro(
    registry: PatternRegistry,
    candidate_patterns: set[ExpandedClassPattern],
    verb: dict[str, str],
):
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]
    present_verb_forms = [f for f in forms if verb.get(f)]

    definition = verb.get("definition", "unknown")

    matches = []
    # Group by Macro for preference logic
    macro_groups = defaultdict(list)
    for p in sorted(candidate_patterns, key=lambda p: registry.key_for_pattern(p)):
        macro_groups[p.macro_name()].append(p)

    for group_name, patterns in macro_groups.items():
        # LOGIC COPIED FROM OLD get_matches_for_verb TO PRETAIN SELECTION BEHAVIOR

        # 1. Pruning: Group patterns by their signature on PRESENT forms
        buckets = defaultdict(list)
        for p in patterns:
            signature = tuple(p.get(f) for f in present_verb_forms)
            buckets[signature].append(p)

        candidates = []
        for sig, group_patterns in buckets.items():
            # Pick simplest (lowest specificity)
            best = min(
                group_patterns,
                key=lambda x: sum(1 for f in forms if x.get(f)),
            )
            candidates.append(best)

        # 2. Sorting: Sort candidates by Specificity DESCENDING
        candidates.sort(key=lambda x: sum(1 for f in forms if x.get(f)), reverse=True)

        # 3. Matching
        for cls in candidates:
            class_id = cls.name

            # Check Ending Match (Already mostly done by lookup/intersect, but verifying specifics like * or @)
            all_endings_match = True
            for form in forms:
                if not cls.match_ending(verb, form) and not (
                    form == "imperative" and cls.match_alternated_endings(verb, form)
                ):
                    all_endings_match = False
                    break

            if not all_endings_match:
                continue

            matches.append(
                {
                    "definition": definition,
                    "class": class_id,
                }
            )

    return matches


def get_matches_for_verb(verb, registry: PatternRegistry):
    # 1. OPTIMIZED LOOKUP
    candidate_patterns = registry.get_candidates_combined(verb)

    matches = group_matches_by_macro(registry, candidate_patterns, verb)

    return matches


def identify_aspect_classes(classes_path=None):
    """
    Identify aspect classes for all verbs in a corpus.

    Produces a list initial matches of verbs and class endings.

    Inputs:
    * CORPUS_PATH: corpus with tense endings stripped.
    * CLASSES_PATH: aspect classes to use for matching.

    Outputs:
    * CORPUS_NO_ASP_PATH: corpus with aspect stripped.
    * MATCHES_PATH: correspondence of verbs to aspect classes that match endings. Used for analysis.
    """
    # Load classes via Registry
    registry = PatternRegistry.get_instance()
    registry.load_from_csv(classes_path)

    # Access expanded patterns map for looking up full details later if needed
    # But get_matches_for_verb now initiates lookup.

    # For stripping later, we need a map of name -> pattern
    # Let's build a quick map from the registry's patterns
    classes_map = {p.name: p for p in registry.expanded_patterns}

    # Load raw corpus
    corpus_rows = []
    with open(CORPUS_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            corpus_rows.append(row)

    matches_data = []
    stripped_corpus_data: List[StrippedVerbRow] = []

    for verb in corpus_rows:
        matches = get_matches_for_verb(verb, registry)
        for m in matches:
            m["corpus_id"] = verb.get("corpus_id", "")
        matches_data.extend(matches)

        # Identify candidates for stripping
        seen_class_def = set()

        for match in matches:
            key = (match["definition"], match["class"])
            if key in seen_class_def:
                continue
            seen_class_def.add(key)

            cls = classes_map.get(match["class"])
            if cls:
                stripped_corpus_data.append(cls.strip_verb(verb))

    fieldnames = [
        "corpus_id",
        "definition",
        "class",
    ]

    with open(MATCHES_PATH, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches_data)

    if stripped_corpus_data:
        StrippedVerbRow.write_csv(CORPUS_NO_ASP_PATH, stripped_corpus_data)

    print(f"Matches written to {MATCHES_PATH}")
    print(f"Endings Stripped Corpus written to {CORPUS_NO_ASP_PATH}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify verbs using King's classes.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    identify_aspect_classes(args.classes)
