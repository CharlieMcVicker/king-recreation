from typing import List, Dict, Optional, Tuple
from king_recreation.phonology_data import (
    use_glottal_grade,
    VerbConfig,
)
from king_recreation.class_patterns import ClassPatterns


def get_root_candidate(stem: str, ending_pattern: str) -> Optional[str]:
    """
    Statically strips class endings from a stem.
    Does NOT apply * or @ modifiers; these are handled by consistency
    checks and reconstruction logic.
    """
    if not ending_pattern:
        return stem

    literal_ending = ending_pattern.replace("*", "").replace("@", "")

    # If there's a literal ending, stem must end with it
    if literal_ending and not stem.endswith(literal_ending):
        return None

    # Strip literal ending
    root = stem[: -len(literal_ending)] if literal_ending else stem
    return root


def check_root_consistency(
    stem_row: Dict[str, str], class_info: ClassPatterns
) -> Tuple[bool, Optional[str], List[str]]:
    """
    Verifies if all available forms in stem_row yield the same root for a given King Class.
    Accounts for expected truncation from * (1 char) and @ (2 chars) rules.
    Returns (is_consistent, root, mismatch_details).
    """
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]
    mismatch_details = []

    # Extract metadata for set identification
    config = VerbConfig.from_row(stem_row)

    h_candidate_stem = stem_row["present"]
    g_candidate_stem = (
        stem_row.get("present_1sg")
        if use_glottal_grade("present_1sg", config.pron)
        else None
    )

    stem_grades = (
        [h_candidate_stem]
        if g_candidate_stem is None
        else [h_candidate_stem, g_candidate_stem]
    )

    pattern = class_info.get("present", "")

    roots = []
    for stem in stem_grades:
        root = get_root_candidate(stem, pattern)
        if root is None:
            mismatch_details.append(f"{stem}/{pattern} ({'present'}): Suffix mismatch")
            continue

        if "*" in pattern:
            raise Exception("Did not expect * in present pattern")
        elif "@" in pattern:
            raise Exception("Did not expect @ in present pattern")

        roots.append(root)

    if not roots:
        if mismatch_details:
            return False, None, mismatch_details
        return False, None, ["No forms available to extract root"]

    h_root = roots[0]
    g_root = roots[1] if len(roots) == 2 else None

    is_consistent = True
    for fn in forms:
        stem = stem_row.get(fn)
        if not stem:
            continue

        use_g = use_glottal_grade(fn, config.pron)
        target_root = g_root if use_g else h_root

        pattern = class_info.get("present" if fn == "present_1sg" else fn, "")
        root_from_stem = get_root_candidate(stem, pattern)

        # Determine truncation depth for pattern
        form_depth = 0
        if "*" in pattern:
            form_depth = 1
        elif "@" in pattern:
            form_depth = 2

        truncated_target = target_root[:-form_depth] if form_depth > 0 else target_root

        if root_from_stem != truncated_target:
            is_consistent = False
            if form_depth > 0:
                mismatch_details.append(
                    f"{fn}: Truncation mismatch (got '{root_from_stem}', expected '{truncated_target}' as {form_depth}-char truncation of '{target_root}')"
                )
            else:
                mismatch_details.append(
                    f"{fn}: Root mismatch (got '{root_from_stem}', expected '{truncated_target}')"
                )

    if is_consistent:
        return True, h_root, []

    return False, None, mismatch_details
