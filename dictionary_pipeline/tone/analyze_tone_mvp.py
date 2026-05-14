from csv import DictWriter

from dictionary_pipeline.paths import UNDERLYING_STEMS_PATH
from dictionary_pipeline.tone.analysis import (
    check_prediction,
    generate_underlying_forms,
    get_tonicity_for_form,
)
from dictionary_pipeline.tone.data_loader import FORMS, load_data, write_elligible_verbs
from dictionary_pipeline.tone.diagnostics import (
    analyze_class_coverage,
    calculate_prediction_stats,
)


def predict_underlying_form(verb, forms, form_name):
    # Determine the tone sequence for the given form
    form_str = forms[form_name]
    tonicity = get_tonicity_for_form(verb, form_name)
    return generate_underlying_forms(form_str, tonicity=tonicity)


def main():
    verbs, cnd_corpus, corpus_id_to_entries = load_data()

    # Get eligible verbs and their surface stems
    verbs_with_forms = write_elligible_verbs(verbs, cnd_corpus, corpus_id_to_entries)

    output_rows = []
    for verb, row in verbs_with_forms:
        corpus_id = row["corpus_id"]
        for fn in FORMS:
            surface_stem = row.get(fn)
            if not surface_stem:
                continue
            tonicity = get_tonicity_for_form(verb, fn)
            underlying_candidates = generate_underlying_forms(
                surface_stem, tonicity=tonicity
            )
            for uf in underlying_candidates:
                if check_prediction(str(uf), surface_stem, tonicity=tonicity):
                    output_rows.append(
                        {
                            "corpus_id": corpus_id,
                            "definition": verb.definition,
                            "class": verb.morphology.class_name,
                            "form": fn,
                            "surface_stem": surface_stem,
                            "underlying_stem": str(uf),
                        }
                    )

    if output_rows:
        with open(UNDERLYING_STEMS_PATH, "w", newline="") as f:
            writer = DictWriter(
                f,
                fieldnames=[
                    "corpus_id",
                    "definition",
                    "class",
                    "form",
                    "surface_stem",
                    "underlying_stem",
                ],
            )
            writer.writeheader()
            writer.writerows(output_rows)
        print(f"Underlying stems written to {UNDERLYING_STEMS_PATH}")

    # Analyze class coverage
    analyze_class_coverage(verbs_with_forms)

    # Calculate overall prediction stats and generate charts
    calculate_prediction_stats(verbs_with_forms)

    # Verification of a few entries
    if verbs_with_forms and False:
        print("\nVerification of a few eligible verbs:")
        for verb, row in verbs_with_forms[:5]:
            print(f"\nVerb: {verb.definition} (Root: {verb.h_grade_root})")
            for fn in ["present", "perfective"]:
                surface = row.get(fn)
                if not surface:
                    continue

                # Generate underlying forms
                tonicity = get_tonicity_for_form(
                    verb, fn
                )  # Changed from form_name to fn
                underlying_candidates = generate_underlying_forms(
                    surface, tonicity=tonicity
                )
                print(f"  Form: {fn:12} Surface: {surface:15}")
                for i, uf in enumerate(
                    underlying_candidates[:2]
                ):  # Show first 2 candidates
                    reconstructed = infer_surface_forms(uf, tonicity=tonicity)
                    target_mask = strip_morpheme_boundaries(surface)
                    match = any(
                        target_mask == strip_morpheme_boundaries(r)
                        for r in reconstructed
                    )
                    print(
                        f"    Candidate {i+1}: {str(uf):15} | Reconstructed: {reconstructed[0][:20]}... | Match: {match}"
                    )
                if len(underlying_candidates) > 2:
                    print(f"    ({len(underlying_candidates)-2} more candidates...)")


if __name__ == "__main__":
    main()
