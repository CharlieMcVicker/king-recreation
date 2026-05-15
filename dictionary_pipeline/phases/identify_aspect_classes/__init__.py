from collections import defaultdict

from dictionary_pipeline.dictionary_forms import ALL_FORM_NAMES, get_form_spec
from dictionary_pipeline.phases.identify_aspect_classes.artifacts import (
    StrippedVerbRow,
    save_matches,
    save_stripped_corpus,
)
from dictionary_pipeline.phases.preprocess_ced.artifacts import load_corpus
from dictionary_pipeline.row_models import AspectInfo, CorpusForms, VerbMeta
from morphology.morphemes.aspect.class_patterns import ExpandedClassPattern
from morphology.morphemes.aspect.pattern_registry import PatternRegistry


def strip_verb_forms(
    cls: ExpandedClassPattern, verb: dict[str, str]
) -> StrippedVerbRow:
    """
    Dictionary-aware function: iterates over dictionary form-name columns
    and uses the morphological strip_form() to remove aspect suffixes.
    """
    stripped_row = StrippedVerbRow(
        meta=VerbMeta(
            corpus_id=verb.get("corpus_id", ""),
            definition=verb.get("definition", ""),
        ),
        aspect=AspectInfo(
            verb_class=cls.name,
            stative=(cls.parent_name == "stative"),
        ),
        forms=CorpusForms(),
    )

    for fn in ALL_FORM_NAMES:
        form_val = verb.get(fn)
        if not form_val:
            continue

        form_spec = get_form_spec(fn)
        aspect = form_spec.aspect

        stripped_stem = cls.strip_form(aspect, form_val)
        if stripped_stem is not None:
            setattr(stripped_row.forms, fn, stripped_stem)

    return stripped_row


def group_matches_by_macro(
    registry: PatternRegistry,
    candidate_patterns: set[ExpandedClassPattern],
    verb: dict[str, str],
) -> list[dict[str, str]]:
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


def get_matches_for_verb(
    verb: dict[str, str], registry: PatternRegistry
) -> list[dict[str, str]]:
    # 1. Prepare form tuples for candidate lookup
    form_tuples = []
    for fn in ALL_FORM_NAMES:
        surface_form = verb.get(fn)
        if not surface_form:
            continue

        form_spec = get_form_spec(fn)

        # "Cheese" the alternation logic: allow suffix alternation for present_1sg and imperative
        allow_alt = fn in ["present_1sg", "imperative"]

        form_tuples.append((surface_form, form_spec.aspect, allow_alt))

    # 2. OPTIMIZED LOOKUP
    candidate_patterns = registry.get_candidates_combined(form_tuples)

    matches = group_matches_by_macro(registry, candidate_patterns, verb)

    return matches


def identify_aspect_classes(classes_path: str | None = None) -> None:
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
    corpus_rows = load_corpus()

    matches_data = []
    stripped_corpus_data: list[StrippedVerbRow] = []

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
                stripped_corpus_data.append(strip_verb_forms(cls, verb))

    save_matches(matches_data)

    if stripped_corpus_data:
        save_stripped_corpus(stripped_corpus_data)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify verbs using King's classes.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    identify_aspect_classes(args.classes)
