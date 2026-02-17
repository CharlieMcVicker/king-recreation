import csv
import json
import os
from typing import List

from king_recreation.morphemes.prefixes import PrefixConfig
from king_recreation.morphemes.prefixes.pronominals import use_glottal_grade
from king_recreation.paths import (
    CONSISTENCY_ANALYSIS_PATH,
    CORPUS_NO_PRE_NO_ASP_PATH,
    CORPUS_PATH,
    RECONSTRUCTION_FAILURES_PATH,
    RECONSTRUCTION_REPORT_PATH,
    RECONSTRUCTION_VALIDATION_PATH,
    REPORTS_PATH,
    VALIDATED_MATCHES_PATH,
    VALIDATED_RECONSTRUCTABLE_ROOTS_PATH,
)
from king_recreation.reconstruction import (
    ReconstructableVerb,
    ReconstructionEngine,
    desegment,
)


def reconstruct_and_validate(classes_path=None):
    """
    Reconstruct verbs from derived roots and validate against the original corpus.

    This phase takes the identifying prefixes and aspect classes and attempts to
    re-generate the original surface forms. Matches are validated and saved.

    Inputs:
    * CORPUS_NO_PRE_NO_ASP_PATH: Derived roots with prefixes and aspect stripped.
    * CORPUS_PATH: Original corpus for validation reference.
    * VALIDATED_RECONSTRUCTABLE_ROOTS_PATH: (Optional) Previous user selections to persist.

    Outputs:
    * VALIDATED_RECONSTRUCTABLE_ROOTS_PATH: Successfully reconstructed roots.
    * RECONSTRUCTION_FAILURES_PATH: Verbs that failed reconstruction.
    * RECONSTRUCTION_REPORT_PATH: Detailed report of ambiguous/failed items.
    * VALIDATED_MATCHES_PATH: Simple list of validated matches (corpus_id, class).
    * CONSISTENCY_ANALYSIS_PATH: Report on internal consistency of derived roots.
    """
    engine = ReconstructionEngine(classes_path)

    # Load Derived Roots
    derived_roots = []
    if os.path.exists(CORPUS_NO_PRE_NO_ASP_PATH):
        with open(CORPUS_NO_PRE_NO_ASP_PATH, "r", encoding="utf-8") as f:
            derived_roots = list(csv.DictReader(f))
    else:
        print(f"Error: {CORPUS_NO_PRE_NO_ASP_PATH} not found.")
        return

    # Load existing validated roots to persist user selections
    user_selected_rows = []
    if os.path.exists(VALIDATED_RECONSTRUCTABLE_ROOTS_PATH):
        with open(VALIDATED_RECONSTRUCTABLE_ROOTS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "user_selected" in reader.fieldnames:
                for row in reader:
                    if row.get("user_selected") == "x":
                        user_selected_rows.append(row)

    print(f"Loaded {len(user_selected_rows)} user-selected rows for persistence.")

    # Load raw Corpus
    full_corpus_map = {}
    with open(CORPUS_PATH, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            full_corpus_map[row["corpus_id"]] = row

    reconstructable_verbs: list[ReconstructableVerb] = []
    consistency_analysis = []
    forms = [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]

    for stem_row in derived_roots:
        definition = stem_row["definition"]
        cls_name = stem_row["class"]

        config = PrefixConfig.from_row(stem_row)

        # Optional: We could re-verify consistency here, but derive_stems checks it.
        # We assume if it's in derived_roots, it passed basic consistency.

        post_root_morpheme = stem_row["post_root_morpheme"]
        post_root_morpheme = post_root_morpheme if post_root_morpheme else None

        h_root = stem_row["h_grade"]

        glottal_root = None
        if use_glottal_grade("present_1sg", config.pron, config.stative):
            glottal_root = stem_row["g_grade"]

            if glottal_root == "" and not h_root == "":
                glottal_root = None

        verb = ReconstructableVerb(
            definition=definition,
            h_grade_root=h_root,
            glottal_grade_root=glottal_root,
            class_name=cls_name,
            post_root_morpheme=post_root_morpheme,
            config=config,
            corpus_id=int(stem_row["corpus_id"]) if "corpus_id" in stem_row else None,
            original_data=stem_row,
        )
        reconstructable_verbs.append(verb)

    print(
        f"Found {len(reconstructable_verbs)} reconstructable candidates from derived roots."
    )

    # Validation Phase
    success_count = 0
    failures = []
    report_data = []
    validated_verbs: List[ReconstructableVerb] = []
    validated_rows: List[dict] = []

    for verb in reconstructable_verbs:
        generated_sets = engine.reconstruct_verb(verb)
        matches_all = True
        failed_forms = []
        ref = (
            full_corpus_map.get(str(verb.corpus_id))
            if verb.corpus_id is not None
            else None
        )
        if not ref:
            # Fallback for old data or edge cases
            ref = full_corpus_map.get(verb.definition)

        if ref:
            verb.entry_no = (lambda x: int(x) if x is not None else None)(
                ref.get("entry_no", None)
            )

        # Capture options for report
        options = generated_sets[0] if generated_sets else {fn: set() for fn in forms}

        desegmented_forms = {
            fn: {desegment(s): s for s in options.get(fn, {})} for fn in options
        }

        segmented_forms = {}

        if not generated_sets:
            matches_all = False
            failed_forms = ["Generation Failed"]
        else:
            for fn in forms:
                ref_word = ref.get(fn)
                if not ref_word:
                    continue
                if ref_word not in desegmented_forms.get(fn, set()):
                    matches_all = False
                    failed_forms.append(
                        f"{fn}: expected '{ref_word}', got {sorted(list(desegmented_forms.get(fn, set())))}"
                    )
                else:
                    segmented = desegmented_forms[fn][ref_word]
                    segmented_forms[fn] = segmented

        if matches_all:
            success_count += 1
            verb.segmented_forms = segmented_forms
            validated_verbs.append(verb)
            # Inject entry_no into original_data so it persists to the CSV
            if verb.entry_no is not None:
                verb.original_data["entry_no"] = verb.entry_no

            # Inject segmented_forms into original_data so it persists to the CSV
            verb.original_data["segmented_forms"] = json.dumps(
                verb.segmented_forms, ensure_ascii=False
            )

            # Check if this matches a user selected row
            # We match on all fields except user_selected and entry_no to be safe,
            # or simply use the fact that original_data might match if it hasn't changed.
            # However, ReconstructableVerb reconstructs data which might differ slightly if logic changes.
            # But the requirement is: "fail when rewriting if we would drop a row that was user marked"
            # This implies the row must be EXACTLY valid as per current logic.
            # So we check if the currently generated `verb.original_data` (augmented with keys)
            # matches the critical fields of a saved user_selection.

            # Let's match on specific identity fields to be robust:
            # corpus_id, definition, class, h_grade, g_grade, post_root_morpheme

            def get_identity_key(r):
                return (
                    str(r.get("corpus_id", "")),
                    r.get("class", ""),
                    r.get("h_grade", ""),
                    r.get("g_grade", ""),
                    r.get("post_root_morpheme", "") or "",
                    # Add all configuration fields to be specific
                    r.get("metathesis_involved", ""),
                    r.get("set_a_b", ""),
                    r.get("stem_type", ""),
                    r.get("metathesis_strategy", ""),
                    r.get("middle_voice", ""),
                    r.get("ka_variant", ""),
                    r.get("aki_1st", ""),
                    r.get("uwa_v", ""),
                    r.get("3rd_person_object", ""),
                    r.get("translocutive", ""),
                    r.get("translocutive_imp_only", ""),
                    r.get("partitive", ""),
                    r.get("distributive", ""),
                    r.get("distributive_fut_prog", ""),
                )

            current_key = get_identity_key(verb.original_data)

            # This implementation is O(N*M) which is fine for small N, M (~2000 rows).
            # If slow, optimize to set lookup.
            is_selected = False
            for usr_row in user_selected_rows:
                if get_identity_key(usr_row) == current_key:
                    is_selected = True
                    break

            if is_selected:
                verb.original_data["user_selected"] = "x"
            else:
                verb.original_data["user_selected"] = ""

            validated_rows.append(verb.original_data)
        else:
            failures.append(
                {
                    "definition": verb.definition,
                    "failed_forms": failed_forms,
                    "class": verb.class_name,
                    "corpus_id": verb.corpus_id,
                }
            )

        # Add to report data
        ambiguous_forms = [fn for fn, opts in options.items() if len(opts) > 1]
        report_data.append(
            {
                "definition": verb.definition,
                "class": verb.class_name,
                "root": verb.h_grade_root,  # Use h-grade as primary for report
                "success": matches_all,
                "ambiguous_forms": ";".join(ambiguous_forms),
                "notes": (
                    "Ambiguity implies lossy rule reversal" if ambiguous_forms else ""
                ),
            }
        )

    print(f"Validation Success: {success_count}/{len(reconstructable_verbs)}")

    # Save Consistency Analysis
    analysis_fields = [
        "definition",
        "assigned_class",
        "is_consistent",
        "mismatch_details",
    ] + [f"root_{fn}" for fn in forms]
    with open(CONSISTENCY_ANALYSIS_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=analysis_fields)
        writer.writeheader()
        writer.writerows(consistency_analysis)

    # Save Matches Validated
    validated_matches_data = []
    for d, verb in zip(report_data, reconstructable_verbs):
        if d["success"]:
            validated_matches_data.append(
                {
                    "corpus_id": verb.corpus_id,
                    "definition": d["definition"],
                    "class": d["class"],
                    "scope": "reconstructs",
                }
            )

    if validated_matches_data:
        keys = ["corpus_id", "definition", "class", "scope"]
        with open(VALIDATED_MATCHES_PATH, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(validated_matches_data)

    # Save Reconstruction Report
    with open(RECONSTRUCTION_REPORT_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "definition",
                "class",
                "root",
                "success",
                "ambiguous_forms",
                "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(report_data)

    with open(RECONSTRUCTION_VALIDATION_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": f"{success_count}/{len(reconstructable_verbs)}",
                "failures": failures,
            },
            f,
            indent=4,
        )

    # Save Validated Roots CSV
    if validated_rows:
        # Re-determine fieldnames to include entry_no if it was added
        # (It effectively merges keys from all rows to handle optional entry_no)
        all_keys = set()
        for row in validated_rows:
            all_keys.update(row.keys())

        # Verify all user selections were preserved
        missing_selections = []

        # Build set of generated identity keys
        def get_identity_key_simple(r):
            return (
                str(r.get("corpus_id", "")),
                r.get("class", ""),
                r.get("h_grade", ""),
                r.get("g_grade", ""),
                r.get("post_root_morpheme", "") or "",
                # Add all configuration fields to be specific
                r.get("metathesis_involved", ""),
                r.get("set_a_b", ""),
                r.get("stem_type", ""),
                r.get("metathesis_strategy", ""),
                r.get("middle_voice", ""),
                r.get("ka_variant", ""),
                # r.get("long_start", ""),
                r.get("aki_1st", ""),
                r.get("uwa_v", ""),
                r.get("3rd_person_object", ""),
                r.get("translocutive", ""),
                r.get("translocutive_imp_only", ""),
                r.get("partitive", ""),
                r.get("distributive", ""),
                r.get("distributive_fut_prog", ""),
            )

        generated_keys = {get_identity_key_simple(r) for r in validated_rows}

        for usr_row in user_selected_rows:
            if get_identity_key_simple(usr_row) not in generated_keys:
                missing_selections.append(usr_row)

        if missing_selections:
            print(
                "[ERROR] The following user-selected rows are no longer valid or generated:"
            )
            for row in missing_selections:
                print(f"  - ID: {row.get('corpus_id')}, Root: {row.get('h_grade')}")
            print("Aborting save to prevent data loss.")
            exit(1)

        fieldnames = [
            "corpus_id",
            "entry_no",
            "user_selected",
            "definition",
            "stative",
            "class",
            "post_root_morpheme",
            "h_grade",
            "g_grade",
            "metathesis_involved",
            "set_a_b",
            "stem_type",
            "metathesis_strategy",
            "middle_voice",
            "plural",
            "ka_variant",
            "aki_1st",
            "uwa_v",
            "3rd_person_object",
            "translocutive",
            "translocutive_imp_only",
            "partitive",
            "distributive",
            "distributive_fut_prog",
            "segmented_forms",
        ]

        # Ensure standard order of important columns if possible, but taking from first row is standard here
        # Make sure optional columns are present
        for col in ["entry_no", "user_selected"]:
            if col not in fieldnames and col in all_keys:
                fieldnames.append(col)

        with open(
            VALIDATED_RECONSTRUCTABLE_ROOTS_PATH, "w", encoding="utf-8", newline=""
        ) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(validated_rows)

    # Save Reconstruction Failures CSV
    # failure format: {"definition": ..., "failed_forms": [...], "class": ...}
    failures_csv_data = []
    for fail in failures:
        failures_csv_data.append(
            {
                "corpus_id": fail["corpus_id"],
                "definition": fail["definition"],
                "class": fail["class"],
                "mismatch_details": "; ".join(fail["failed_forms"]),
            }
        )

    # Sort for stability
    failures_csv_data.sort(
        key=lambda x: (x["class"], x["definition"], x["corpus_id"] or 0)
    )

    with open(RECONSTRUCTION_FAILURES_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["corpus_id", "definition", "class", "mismatch_details"],
        )
        writer.writeheader()
        writer.writerows(failures_csv_data)

    print(f"Artifacts saved to {REPORTS_PATH}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reconstruct verbs from roots.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    reconstruct_and_validate(args.classes)
