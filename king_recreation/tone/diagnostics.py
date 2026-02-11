import os
from csv import DictReader

from king_recreation.tone.analysis import (
    check_prediction,
    generate_underlying_forms,
    get_tonicity_for_form,
)
from king_recreation.tone.models import LocalHighTone, Tonicity


def diagnose_mismatch(
    verb, surface, expected_ending, tonicity: Tonicity = Tonicity.TONIC
):
    print(f"    Mismatch: {verb.definition[:30]}... | Surface: {surface}")

    underlying_candidates = generate_underlying_forms(surface, tonicity=tonicity)
    valid_candidates = [
        str(uf)
        for uf in underlying_candidates
        if check_prediction(str(uf), surface, tonicity=tonicity)
    ]

    # 1. Check for Length or quality Mismatch (Valid UF exists but different ending)
    if valid_candidates:
        print(f"      Found {len(valid_candidates)} valid underlying forms:")
        for uf in valid_candidates:
            print(f"        - {uf}")
        # Check if any is 'close' (e.g. length diff)
        # Simplify: just report them. User can see.

    # 2. Check for Start State Blocked (for Imperative/21 tone)
    # Try assuming PREVIOUS High (BLOCKED environment)
    candidates_blocked = generate_underlying_forms(
        surface, initial_lh=LocalHighTone.PREV, tonicity=tonicity
    )
    valid_blocked = [
        str(uf)
        for uf in candidates_blocked
        if check_prediction(
            str(uf),
            surface,
            initial_lh=LocalHighTone.PREV,
            tonicity=tonicity,
        )
    ]

    found_blocked_match = False
    for uf in valid_blocked:
        if uf.endswith(expected_ending):
            found_blocked_match = True
            break

    if found_blocked_match:
        print(
            f"      [DIAGNOSIS] Matches expected ending '{expected_ending}' IF we assume 'BLOCKED' environment (Preceding High Tone)."
        )
        return

    if not valid_candidates and not found_blocked_match:
        print(
            "      [DIAGNOSIS] No valid underlying forms found even with BLOCKED check."
        )


def analyze_class_coverage(verbs_with_forms):
    print("\n--- Class Coverage Analysis ---")

    # Load underlying class definitions
    class_defs = {}
    # Assuming running from repo root
    underlying_classes_path = "data/classes_underlying.csv"
    if not os.path.exists(underlying_classes_path):
        print(f"File not found: {underlying_classes_path}")
        return

    with open(underlying_classes_path, "r") as f:
        reader = DictReader(f)
        for row in reader:
            class_defs[row["class"]] = row

    target_class = "go"
    if target_class not in class_defs:
        print(f"Class '{target_class}' not found in {underlying_classes_path}")
        return

    target_def = class_defs[target_class]

    # Filter for verbs of the target class
    class_verbs = [
        (v, row) for v, row in verbs_with_forms if v.class_name == target_class
    ]

    total_verbs = len(class_verbs)
    if total_verbs == 0:
        print(f"No verbs found for class '{target_class}'")
        return

    print(f"Analyzing {total_verbs} verbs of class '{target_class}'")

    # Forms to check (intersection of FORMS and columns in CSV)
    forms_to_check = [
        f
        for f in ["present", "imperfective", "perfective", "imperative", "infinitive"]
        if f in target_def and target_def[f].strip()
    ]

    for form_name in forms_to_check:
        # Get target endings
        raw_endings = target_def[form_name]
        target_endings = [e.strip() for e in raw_endings.split(";") if e.strip()]

        if not target_endings:
            continue

        print(f"\nForm: {form_name}")

        for ending in target_endings:
            match_count = 0
            valid_verbs_for_form = 0

            for verb, row in class_verbs:
                surface = row.get(form_name)
                if not surface:
                    continue

                valid_verbs_for_form += 1

                # Generate underlying forms
                tonicity = get_tonicity_for_form(verb, form_name)
                underlying_candidates = generate_underlying_forms(
                    surface, tonicity=tonicity
                )

                # Check if ANY valid underlying form ends with the target ending
                matches_ending = False
                for uf in underlying_candidates:
                    # Check if candidate is valid (reconstructs surface)
                    if not check_prediction(str(uf), surface, tonicity=tonicity):
                        continue

                    # Check ending match
                    # We use str(uf) which is the string representation of LexedForm
                    if str(uf).endswith(ending):
                        matches_ending = True
                        break

                if matches_ending:
                    match_count += 1
                else:
                    diagnose_mismatch(verb, surface, ending, tonicity=tonicity)

            if valid_verbs_for_form > 0:

                percentage = (match_count / valid_verbs_for_form) * 100
                print(
                    f"  Ending '{ending}': {match_count}/{valid_verbs_for_form} ({percentage:.1f}%)"
                )
            else:
                print(f"  Ending '{ending}': No valid surface forms found.")
