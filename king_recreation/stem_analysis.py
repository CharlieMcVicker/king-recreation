from typing import List, Dict, Optional, Tuple
from king_recreation.phonology_data import (
    use_glottal_grade,
    VerbConfig,
)


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
    stem_row: Dict[str, str], class_info: Dict[str, str]
) -> Tuple[bool, Optional[str], List[str]]:
    """
    Verifies if all available forms in stem_row yield the same root for a given King Class.
    Accounts for expected truncation from * (1 char) and @ (2 chars) rules.
    Returns (is_consistent, root, mismatch_details).
    """
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]
    candidate_data = []  # List of (form, root, depth)
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

    for stem in stem_grades:
        root = get_root_candidate(stem, pattern)
        if root is None:
            mismatch_details.append(f"{stem}/{pattern} ({'present'}): Suffix mismatch")
            continue

        # Determine truncation depth
        depth = 0
        if "*" in pattern:
            depth = 1
        elif "@" in pattern:
            depth = 2

        candidate_data.append((root, depth))

    if not candidate_data:
        if mismatch_details:
            return False, None, mismatch_details
        return False, None, ["No forms available to extract root"]

    h_root, h_root_depth = candidate_data[0]
    g_root, g_root_depth = (
        candidate_data[1] if len(candidate_data) == 2 else [None, None]
    )

    is_consistent = True
    for fn in forms:
        stem = stem_row.get(fn)
        if not stem:
            continue

        use_g = use_glottal_grade(fn, config.pron)
        target_root = g_root if use_g else h_root
        target_depth = g_root_depth if use_g else h_root_depth

        pattern = class_info.get("present" if fn == "present_1sg" else fn, "")
        root_from_stem = get_root_candidate(stem, pattern)
        # Determine truncation depth
        form_depth = 0
        if "*" in pattern:
            form_depth = 1
        elif "@" in pattern:
            form_depth = 2

        # if the reference has more cut off than the form that is too bad
        depth_diff = form_depth - target_depth
        if depth_diff < 0:
            is_consistent = False
            mismatch_details.append(f"{fn}: Unexpectedly longer than target")
            continue

        truncated_target = target_root[:-form_depth] if form_depth > 0 else target_root
        truncated_stem_root = (
            root_from_stem[:-target_depth] if target_depth > 0 else root_from_stem
        )

        if "swelling" in stem_row.get("definition", ""):
            print(class_info.get("class"), stem, root_from_stem, target_root)
            print("\t\t\t", truncated_stem_root, truncated_target)

        if truncated_stem_root != truncated_target:
            is_consistent = False
            if depth_diff > 0:
                mismatch_details.append(
                    f"{fn}: Truncation mismatch (got '{root}', expected '{truncated_target}' as {depth_diff}-char truncation of '{target_root}')"
                )
            else:
                mismatch_details.append(
                    f"{fn}: Root mismatch (got '{root}', expected '{truncated_target}')"
                )

    if is_consistent:
        return True, h_root, []

    return False, None, mismatch_details
