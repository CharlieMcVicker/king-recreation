import json
from typing import Any

from dictionary_pipeline.dictionary_forms import (
    FORM_NAMES_FOR_PREDICTION,
    DictionaryVerb,
    Prediction,
    build_wordspec,
)
from dictionary_pipeline.phases.identify_prefixes.artifacts import load_stripped_roots
from dictionary_pipeline.phases.preprocess_ced.artifacts import load_corpus
from dictionary_pipeline.phases.reconstruct_and_validate.artifacts import (
    load_existing_validated_roots,
    save_consistency_analysis,
    save_reconstruction_failures,
    save_reconstruction_report,
    save_reconstruction_validation,
    save_validated_matches,
    save_validated_roots,
)
from morphology.morphemes.prefixes import PrefixConfig
from morphology.morphemes.prefixes.pronominals import use_glottal_grade
from morphology.reconstruction import MorphologicalVerb, ReconstructionEngine, desegment


def reconstruct_and_validate(
    classes_path: str | None = None, allow_drops: bool = False
) -> None:
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
    derived_roots = load_stripped_roots()
    if derived_roots is None:
        print("Error: Derived roots not found.")
        return

    # Load existing validated roots to persist user selections
    user_selected_rows = load_existing_validated_roots()
    print(f"Loaded {len(user_selected_rows)} user-selected rows for persistence.")

    # Load raw Corpus
    corpus = load_corpus()
    full_corpus_map = {row.meta.corpus_id: row for row in corpus}

    dictionary_verbs: list[DictionaryVerb] = []
    consistency_analysis = []
    for stem_row in derived_roots:
        definition = stem_row["definition"]
        cls_name = stem_row["class"]

        config = PrefixConfig.from_row(stem_row)

        post_root_morpheme = stem_row["post_root_morpheme"]
        post_root_morpheme = post_root_morpheme if post_root_morpheme else None

        h_root = stem_row["h_grade"]

        prediction = Prediction(stem_row.get("prediction", "FullEventful"))
        glottal_root = None
        spec_1sg = build_wordspec(prediction, config.pron, "present_1sg")
        if use_glottal_grade(spec_1sg.person, spec_1sg.number, spec_1sg.pronominal_set):
            glottal_root = stem_row["g_grade"]

            if glottal_root == "" and not h_root == "":
                glottal_root = None

        morphology = MorphologicalVerb(
            h_grade_root=h_root,
            glottal_grade_root=glottal_root,
            class_name=cls_name,
            post_root_morpheme=post_root_morpheme,
            config=config,
        )

        verb = DictionaryVerb(
            definition=definition,
            morphology=morphology,
            corpus_id=int(stem_row["corpus_id"]) if "corpus_id" in stem_row else None,
            original_data=stem_row,
        )
        dictionary_verbs.append(verb)

    print(
        f"Found {len(dictionary_verbs)} reconstructable candidates from derived roots."
    )

    # Validation Phase
    success_count = 0
    failures = []
    report_data = []
    validated_verbs: list[DictionaryVerb] = []
    validated_rows: list[dict[str, Any]] = []

    for verb in dictionary_verbs:
        # Reconstruct all forms for this verb (dictionary-aware iteration)
        prediction = Prediction(verb.original_data.get("prediction", "FullEventful"))
        forms = FORM_NAMES_FOR_PREDICTION[prediction]
        form_options = {}
        for fn in forms:
            spec = build_wordspec(prediction, verb.morphology.config.pron, fn)
            options = engine.reconstruct_spec(verb.morphology, spec)
            if options:
                form_options[fn] = options
        generated_sets = (
            [{fn: set(opts or []) for fn, opts in form_options.items()}]
            if form_options
            else []
        )
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
                ref.meta.entry_no
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
                ref_word = getattr(ref.forms, fn) if ref else None
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
            def get_identity_key(r: dict[str, Any]) -> tuple[str, ...]:
                def normalize_bool(v: Any) -> str:
                    if (
                        v is None
                        or v == ""
                        or v is False
                        or v == "False"
                        or v == "None"
                    ):
                        return "False"
                    if v is True or v == "True" or v == "x":
                        return "True"
                    return str(v)

                def normalize_str(v: Any) -> str:
                    if v is None:
                        return ""
                    return str(v)

                return (
                    normalize_str(r.get("corpus_id")),
                    normalize_str(r.get("class")),
                    normalize_str(r.get("h_grade")),
                    normalize_str(r.get("g_grade")),
                    normalize_str(r.get("post_root_morpheme")),
                    # Add all configuration fields to be specific
                    normalize_bool(r.get("metathesis_involved")),
                    normalize_str(r.get("set_a_b")),
                    normalize_str(r.get("stem_type")),
                    normalize_bool(r.get("allow_h_metathesis")),
                    normalize_str(r.get("middle_voice")),
                    normalize_bool(r.get("ka_variant")),
                    normalize_bool(r.get("aki_1st")),
                    normalize_bool(r.get("uwa_v")),
                    normalize_bool(r.get("3rd_person_object")),
                    normalize_bool(r.get("translocutive")),
                    normalize_bool(r.get("translocutive_imp_only")),
                    normalize_bool(r.get("partitive")),
                    normalize_bool(r.get("distributive")),
                )

            current_key = get_identity_key(verb.original_data)

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
                    "class": verb.morphology.class_name,
                    "corpus_id": verb.corpus_id,
                }
            )

        # Add to report data
        ambiguous_forms = [fn for fn, opts in options.items() if len(opts) > 1]
        report_data.append(
            {
                "definition": verb.definition,
                "class": verb.morphology.class_name,
                "root": verb.morphology.h_grade_root,  # Use h-grade as primary for report
                "success": matches_all,
                "ambiguous_forms": ";".join(ambiguous_forms),
                "notes": (
                    "Ambiguity implies lossy rule reversal" if ambiguous_forms else ""
                ),
            }
        )

    print(f"Validation Success: {success_count}/{len(dictionary_verbs)}")

    # Save Consistency Analysis
    save_consistency_analysis(consistency_analysis)

    # Save Matches Validated
    validated_matches_data = []
    for d, verb in zip(report_data, dictionary_verbs):
        if d["success"]:
            validated_matches_data.append(
                {
                    "corpus_id": verb.corpus_id,
                    "definition": d["definition"],
                    "class": d["class"],
                    "scope": "reconstructs",
                }
            )

    save_validated_matches(validated_matches_data)

    # Save Reconstruction Report
    save_reconstruction_report(report_data)

    save_reconstruction_validation(
        {
            "summary": f"{success_count}/{len(dictionary_verbs)}",
            "failures": failures,
        }
    )

    # Save Validated Roots CSV
    if validated_rows:
        # Verify all user selections were preserved
        def get_identity_key_simple(r: dict[str, Any]) -> tuple[str, ...]:
            def normalize_bool(v: Any) -> str:
                if v is None or v == "" or v is False or v == "False" or v == "None":
                    return "False"
                if v is True or v == "True" or v == "x":
                    return "True"
                return str(v)

            def normalize_str(v: Any) -> str:
                if v is None:
                    return ""
                return str(v)

            return (
                normalize_str(r.get("corpus_id")),
                normalize_str(r.get("class")),
                normalize_str(r.get("h_grade")),
                normalize_str(r.get("g_grade")),
                normalize_str(r.get("post_root_morpheme")),
                # Add all configuration fields to be specific
                normalize_bool(r.get("metathesis_involved")),
                normalize_str(r.get("set_a_b")),
                normalize_str(r.get("stem_type")),
                normalize_bool(r.get("allow_h_metathesis")),
                normalize_str(r.get("middle_voice")),
                normalize_bool(r.get("ka_variant")),
                normalize_bool(r.get("aki_1st")),
                normalize_bool(r.get("uwa_v")),
                normalize_bool(r.get("3rd_person_object")),
                normalize_bool(r.get("translocutive")),
                normalize_bool(r.get("translocutive_imp_only")),
                normalize_bool(r.get("partitive")),
                normalize_bool(r.get("distributive")),
            )

        generated_keys = {get_identity_key_simple(r) for r in validated_rows}

        missing_selections = []
        for usr_row in user_selected_rows:
            if get_identity_key_simple(usr_row) not in generated_keys:
                missing_selections.append(usr_row)

        if missing_selections:
            print(
                f"[{'WARNING' if allow_drops else 'ERROR'}] The following user-selected rows are no longer valid or generated:"
            )
            for row in missing_selections:
                print(f"  - ID: {row.get('corpus_id')}, Root: {row.get('h_grade')}")
            if not allow_drops:
                print("Aborting save to prevent data loss.")
                exit(1)

        save_validated_roots(validated_rows)

    # Save Reconstruction Failures CSV
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

    save_reconstruction_failures(failures_csv_data)

    print(f"Artifacts saved.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reconstruct verbs from roots.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    reconstruct_and_validate(args.classes)
