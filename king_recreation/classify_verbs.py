from king_recreation.utils import CLASSES_PATH
from king_recreation.phonology_data import _drop_first_h
from king_recreation.class_patterns import ClassPatterns
import csv
import os
from collections import defaultdict


def normalize(s):
    if s is None:
        return ""
    return s.replace("h", "")


def match_ending(corpus_form, pattern_suffix, strict):
    # Policy: Vacuous Matching
    # If the corpus form is missing, it cannot contradict any pattern.
    if not corpus_form:
        return True

    # Literal characters only, ignore * or @
    if pattern_suffix is None:
        pattern_suffix = ""
    literal_suffix = pattern_suffix.replace("*", "").replace("@", "")

    if strict:
        return corpus_form.endswith(literal_suffix)
    else:
        return normalize(corpus_form).endswith(normalize(literal_suffix))


def calculate_stem_final_match(corpus_form, pattern_suffix, stem_finals, strict):
    # Policy: Vacuous Matching
    if not corpus_form:
        return True

    # 1. Identify literal ending
    if pattern_suffix is None:
        pattern_suffix = ""
    literal_suffix = pattern_suffix.replace("*", "").replace("@", "")

    # 2. Strip literal ending (if possible)
    if not corpus_form.endswith(literal_suffix):
        if not strict and normalize(corpus_form).endswith(normalize(literal_suffix)):
            norm_form = normalize(corpus_form)
            norm_suffix = normalize(literal_suffix)
            candidate_stem_norm = (
                norm_form[: -len(norm_suffix)] if len(norm_suffix) > 0 else norm_form
            )
        else:
            return False
    else:
        candidate_stem_raw = (
            corpus_form[: -len(literal_suffix)]
            if len(literal_suffix) > 0
            else corpus_form
        )
        candidate_stem_norm = normalize(candidate_stem_raw)

    # 3. Adjust stem final based on modifiers
    if not stem_finals:
        stem_finals = [""]

    match = False
    for sf in stem_finals:
        sf_adjusted = sf
        if "*" in pattern_suffix:
            if len(sf_adjusted) >= 1:
                sf_adjusted = sf_adjusted[:-1]
        elif "@" in pattern_suffix:
            if len(sf_adjusted) >= 2:
                sf_adjusted = sf_adjusted[:-2]

        # 4. Verify candidate stem
        sf_norm = normalize(sf_adjusted)
        if strict:
            candidate_stem_strict = (
                corpus_form[: -len(literal_suffix)]
                if len(literal_suffix) > 0
                else corpus_form
            )
            if candidate_stem_strict.endswith(sf_adjusted):
                match = True
                break
        else:
            if candidate_stem_norm.endswith(sf_norm):
                match = True
                break
    return match


def get_matches_for_verb(verb, macro_groups):
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]
    matches = []

    definition = verb.get("definition", "unknown")

    # Determine which forms are present in the verb
    present_verb_forms = [f for f in forms if verb.get(f)]

    for group_name, patterns in macro_groups.items():
        # 1. Pruning: Group patterns by their signature on PRESENT forms
        # We want to keep only one representative for patterns that are identical on the forms we can verify.
        # This handles the case where patterns differ only on missing forms.
        buckets = defaultdict(list)
        for p in patterns:
            # unique signature based on values for present forms
            signature = tuple(p.get(f) for f in present_verb_forms)
            buckets[signature].append(p)

        candidates = []
        for sig, group_patterns in buckets.items():
            # In each bucket, pick the "simplest" one (lowest specificity)
            # This avoids returning both ClassA and ClassA[imp] if imp is missing.
            # Specificity = number of non-empty fields
            # We want minimum specificity here.
            best = min(
                group_patterns,
                key=lambda x: sum(1 for f in forms if x.get(f)),
            )
            candidates.append(best)

        # 2. Sorting: Sort candidates by Specificity DESCENDING
        # If we have distinct candidates (differing on present forms),
        # we want to match the most specific one first (e.g. ClassA[imp] vs ClassA if imp is present).
        candidates.sort(key=lambda x: sum(1 for f in forms if x.get(f)), reverse=True)

        # 3. Matching: Find the first match in the sorted candidates
        # Since we sorted by specificity, the first match is the best match for this group.
        # We stop after the first match to avoid returning less specific siblings.
        for cls in candidates:
            class_id = cls.name
            stem_finals = cls.stem_finals

            for strictness in ["strict", "loose"]:
                is_strict_bool = strictness == "strict"

                # Check Ending Match
                all_endings_match = True
                for form in forms:
                    form_val = verb.get(form)
                    if not match_ending(form_val, cls.get(form), is_strict_bool):
                        all_endings_match = False
                        break

                # Calculate Stem Final matches
                sf_matches = {}
                for form in forms:
                    form_val = verb.get(form)
                    sf_matches[f"stem_final_match_{form}"] = calculate_stem_final_match(
                        form_val, cls.get(form), stem_finals, is_strict_bool
                    )

                all_sf_match = all(sf_matches.values())

                if all_endings_match:
                    scope = "ending"
                    if all_sf_match:
                        scope = "full"

                    matches.append(
                        {
                            "definition": definition,
                            "class": class_id,
                            "strictness": strictness,
                            "scope": scope,
                            **sf_matches,
                        }
                    )

    return matches


def classify_verbs(classes_path=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    corpus_path = os.path.join(base_dir, "artifacts", "data", "corpus.csv")
    matches_path = os.path.join(base_dir, "artifacts", "data", "matches_initial.csv")
    stripped_path = os.path.join(
        base_dir, "artifacts", "data", "endings_stripped_corpus.csv"
    )

    if classes_path is None:
        classes_path = CLASSES_PATH

    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        return

    # Load classes
    classes = ClassPatterns.from_csv(classes_path)

    # Group classes by macro (original name)
    macro_groups = defaultdict(list)
    for p in classes.values():
        group_name = p.name.split("[")[0]
        if p._original_data and "class" in p._original_data:
            group_name = p._original_data["class"]
        macro_groups[group_name].append(p)

    # Load raw corpus
    corpus_rows = []
    with open(corpus_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            corpus_rows.append(row)

    matches_data = []

    matches_data = []
    stripped_corpus_data = []

    for verb in corpus_rows:
        matches = get_matches_for_verb(verb, macro_groups)
        matches_data.extend(matches)

        # Identify candidates for stripping
        # We include any match that satisfies strictly the ENDING requirement (scope >= ending)
        # We only care about Strict matches for now for derivation? User prompt: "matches at the endings and full level"
        # Let's include strict ending matches.

        seen_class_def = set()

        for m in matches:
            if m["strictness"] == "strict" and m["scope"] in [
                "ending",
                "full",
                "reconstructs",
            ]:
                # Create stripped row
                key = (m["definition"], m["class"])
                if key in seen_class_def:
                    continue
                seen_class_def.add(key)

                # classes is dict now, direct lookup
                cls_info = classes.get(m["class"])
                if not cls_info:
                    continue

                stripped_row = {
                    "definition": m["definition"],
                    "class": m["class"],
                    "scope": m["scope"],
                    # Pre-populate empty stems
                    "present": "",
                    "present_1sg": "",
                    "imperfective": "",
                    "perfective": "",
                    "imperative": "",
                    "infinitive": "",
                }

                # Strip suffixes
                forms = [
                    "present",
                    "present_1sg",
                    "imperfective",
                    "perfective",
                    "imperative",
                    "infinitive",
                ]
                for fn in forms:
                    # Input is raw corpus, so we look up in `verb` (the corpus row)
                    # Note: corpus.csv might not have present_1sg if not in original data?
                    # corpus.csv has specific columns. `get_matches_for_verb` uses ["present", "imperfective", "perfective", "imperative", "infinitive"]
                    # If present_1sg is in corpus, we use it. If not, it's fine.

                    form_val = verb.get(fn)
                    if not form_val:
                        continue

                    # Get pattern from class
                    # Fallback for present_1sg -> present if not in class (standard behavior)
                    cls_pattern = cls_info.get(fn)
                    if fn == "present_1sg" and not cls_pattern:
                        cls_pattern = cls_info.get("present")

                    if cls_pattern is None:
                        cls_pattern = ""

                    # Strip Literal Suffix
                    literal_suffix = cls_pattern.replace("*", "").replace("@", "")

                    if form_val.endswith(literal_suffix):
                        stripped_stem = (
                            form_val[: -len(literal_suffix)]
                            if literal_suffix
                            else form_val
                        )
                        stripped_row[fn] = stripped_stem

                    # allow forms that might h alternate to alternate _in the ending_
                    elif fn in ["present_1sg", "imperative"]:
                        hless_suffix = _drop_first_h(literal_suffix)
                        if form_val.endswith(hless_suffix):
                            stripped_stem = (
                                form_val[: -len(hless_suffix)]
                                if hless_suffix
                                else form_val
                            )
                            stripped_row[fn] = stripped_stem

                stripped_corpus_data.append(stripped_row)

    fieldnames = [
        "definition",
        "class",
        "strictness",
        "scope",
        "stem_final_match_present",
        "stem_final_match_imperfective",
        "stem_final_match_perfective",
        "stem_final_match_imperative",
        "stem_final_match_infinitive",
    ]

    with open(matches_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches_data)

    if stripped_corpus_data:
        # Determine all keys dynamically or fixed
        keys = list(stripped_corpus_data[0].keys())
        # Ensure all form columns present
        with open(stripped_path, mode="w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(stripped_corpus_data)

    print(f"Matches written to {matches_path}")
    print(f"Endings Stripped Corpus written to {stripped_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Classify verbs using King's classes.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    classify_verbs(args.classes)
