import csv
import os
from collections import defaultdict
from dataclasses import asdict, dataclass
from typing import List

from king_recreation.h_alternation import (
    possible_alternates,
    prevent_C_glottal_cluster,
    recreate_C_glottal_clusters,
)
from king_recreation.morphemes.aspect.strip import StrippedVerbRow, create_stripped_row
from king_recreation.paths import corpus_no_asp_path, corpus_path, matches_path
from king_recreation.pattern_registry import PatternRegistry


def match_alternated_endings(form_val: str, suffix: str, classname: str):
    for alt in possible_alternates(suffix, fix_clusters=False):
        if match_ending(recreate_C_glottal_clusters(form_val), alt):
            return True

    return False


def match_ending(corpus_form, pattern_suffix):
    # Policy: Vacuous Matching
    # If the corpus form is missing, it cannot contradict any pattern.
    if not corpus_form:
        return True

    # Literal characters only, ignore * or @
    if pattern_suffix is None:
        pattern_suffix = ""
    literal_suffix = pattern_suffix.replace("*", "").replace("@", "")

    return corpus_form.endswith(literal_suffix)


def get_candidates_combined(verb, registry: PatternRegistry):
    """
    Get initial candidates by intersecting matches from available forms.
    Returns a set of unique ExpandedClassPattern objects.
    """
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]

    # Identify available forms
    available_forms = [f for f in forms if verb.get(f)]

    if not available_forms:
        return (
            set()
        )  # No forms to match against? Or should we return all? Return none seems safer.

    # Start with candidates from the first available form (usually present)
    primary_form = available_forms[0]
    candidate_set = set(registry.get_candidates(verb.get(primary_form), primary_form))

    # Intersect with other forms to narrow down
    # Optimization: Only intersect if candidate_set is large?
    # For correctness, we must intersect or just union?
    # WAIT. If a pattern matches Present but mismatches Imperfective, it is NOT a match.
    # So intersection is correct for finding patterns that are consistent with ALL present forms.
    # PatternRegistry.get_candidates returns patterns whose LITERAL SUFFIX matches the verb form.
    # If a pattern has Imperfective suffix "abc" and verb has "xyz", it won't be returned by get_candidates(imperf).
    # So yes, Intersection is the way.

    for form in available_forms[1:]:
        matches_for_form = set(
            registry.get_candidates(
                verb.get(form), form, allow_suffix_alternation=(form == "imperative")
            )
        )
        candidate_set.intersection_update(matches_for_form)
        if not candidate_set:
            break

    return candidate_set


def get_matches_for_verb(verb, registry: PatternRegistry):
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]
    matches = []

    definition = verb.get("definition", "unknown")
    present_verb_forms = [f for f in forms if verb.get(f)]

    # 1. OPTIMIZED LOOKUP
    candidate_patterns = get_candidates_combined(verb, registry)

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
                form_val = verb.get(form)
                # Use existing match_ending helper which handles vacuous match
                suffix = cls.get(form)
                if not match_ending(form_val, suffix) and not (
                    form == "imperative"
                    and match_alternated_endings(form_val, suffix, classname=class_id)
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


def classify_verbs(classes_path=None):
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
    with open(corpus_path, mode="r", encoding="utf-8") as f:
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

            stripped_row = create_stripped_row(verb, classes_map, match["class"])
            if stripped_row:
                stripped_corpus_data.append(stripped_row)

    fieldnames = [
        "corpus_id",
        "definition",
        "class",
    ]

    with open(matches_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches_data)

    if stripped_corpus_data:
        StrippedVerbRow.write_csv(corpus_no_asp_path, stripped_corpus_data)

    print(f"Matches written to {matches_path}")
    print(f"Endings Stripped Corpus written to {corpus_no_asp_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify verbs using King's classes.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    classify_verbs(args.classes)
