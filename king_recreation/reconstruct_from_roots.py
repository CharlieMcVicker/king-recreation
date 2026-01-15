from king_recreation.utils import CLASSES_PATH
from king_recreation.phonology_data import grades_are_compatible, _drop_first_h
import os
import csv
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from king_recreation.classify_verbs import get_matches_for_verb
from king_recreation.class_patterns import ClassPatterns
from king_recreation.phonology_data import (
    get_pronominal_set_name,
    PronominalConfig,
    VerbConfig,
    get_prefix_details,
    attach_prefix,
    apply_prepronominal,
    use_glottal_grade,
)
from king_recreation.stem_analysis import get_root_candidate, check_root_consistency


@dataclass
class ReconstructibleVerb:
    definition: str
    h_grade_root: str
    glottal_grade_root: Optional[str]
    class_name: str
    config: VerbConfig
    original_stems: Dict[str, str] = field(default_factory=dict)


class ReconstructionEngine:
    def __init__(self, classes_path: str):
        self.classes = ClassPatterns.from_csv(classes_path)

    # _load_classes_raw removed as it is replaced by ClassPatterns.from_csv

    def generate_pronominal_forms(
        self, stem: str, set_name: str, config: PronominalConfig
    ) -> List[str]:
        prefix, condition = get_prefix_details(set_name, config)

        stems_to_try = [(stem, False)]

        candidates = []
        for s, dropped in stems_to_try:
            res = attach_prefix(s, prefix, condition)
            if res:
                candidates.append(res)
        return candidates

    def reconstruct_verb(self, verb: ReconstructibleVerb) -> List[Dict[str, str]]:
        base_stems = {}
        class_info = self.classes.get(verb.class_name)
        if not class_info:
            return []

        for form_name in [
            "present",
            "present_1sg",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]:
            ending_pattern = class_info.get(form_name, "")
            if form_name == "present_1sg" and not ending_pattern:
                ending_pattern = class_info.present

            literal_ending = ending_pattern.replace("*", "").replace("@", "")

            # Determine Grade
            # Default: h-grade
            glottal_grade_form = use_glottal_grade(form_name, verb.config.pron)
            root_to_use = (
                verb.glottal_grade_root if glottal_grade_form else verb.h_grade_root
            )

            if glottal_grade_form and root_to_use is None:
                # Missing required root for this form
                continue

            if root_to_use is None:
                continue

            modified_root = root_to_use
            if "*" in ending_pattern:
                if len(modified_root) >= 1:
                    modified_root = modified_root[:-1]
            elif "@" in ending_pattern:
                if len(modified_root) >= 2:
                    modified_root = modified_root[:-2]

            # if we need to /h/ alternate but there wasnt an h in the h grade root
            # we need to try to drop it from the ending
            if glottal_grade_form and not "h" in verb.h_grade_root:
                literal_ending = _drop_first_h(literal_ending)

            base_stems[form_name] = modified_root + literal_ending

        form_options = {}
        for fn, stem in base_stems.items():
            set_name = get_pronominal_set_name(fn, verb.config.pron)
            if not set_name:
                candidates = [stem]
            else:
                candidates = self.generate_pronominal_forms(
                    stem, set_name, verb.config.pron
                )

            # Apply Prepronominals
            layered_candidates = []
            for c in candidates:
                layered_candidates.extend(apply_prepronominal(c, verb.config.pre, fn))

            form_options[fn] = layered_candidates

        return [{fn: set(opts or []) for fn, opts in form_options.items()}]


def main(classes_path=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    derived_roots_path = os.path.join(
        base_dir, "artifacts", "data", "derived_roots.csv"
    )
    corpus_path = os.path.join(base_dir, "artifacts", "data", "corpus.csv")

    # We output valid matches here
    matches_output_path = os.path.join(
        base_dir, "artifacts", "data", "matches_validated.csv"
    )

    if classes_path is None:
        classes_path = CLASSES_PATH

    engine = ReconstructionEngine(classes_path)

    # Load Derived Roots
    derived_roots = []
    if os.path.exists(derived_roots_path):
        with open(derived_roots_path, "r", encoding="utf-8") as f:
            derived_roots = list(csv.DictReader(f))
    else:
        print(f"Error: {derived_roots_path} not found.")
        return

    # Load raw Corpus
    full_corpus_map = {}
    with open(corpus_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            full_corpus_map[row["definition"]] = row

    reconstructible_verbs: list[ReconstructibleVerb] = []
    consistency_analysis = []
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]

    for stem_row in derived_roots:
        definition = stem_row["definition"]
        cls_name = stem_row["class"]

        # In derived_roots context, the columns like 'present', 'present_1sg' are already stripped roots
        h_root = stem_row.get("consensus_root")
        if not h_root:
            # Fallback if consensus_root not written (e.g. absent from row? derived_stems writes it)
            h_root = stem_row.get("present")

        config = VerbConfig.from_row(stem_row)

        # Glottal root: If 1sg is glottal (Set A), use the derived 1sg root.
        glottal_root = None
        if use_glottal_grade("present_1sg", config.pron):
            glottal_root = stem_row.get("present_1sg")

        # Optional: We could re-verify consistency here, but derive_stems checks it.
        # We assume if it's in derived_roots, it passed basic consistency.

        verb = ReconstructibleVerb(
            definition=definition,
            h_grade_root=h_root,
            glottal_grade_root=glottal_root,
            class_name=cls_name,
            config=config,
            original_stems={
                fn: stem_row.get(fn, "") for fn in forms
            },  # These are roots now
        )
        reconstructible_verbs.append(verb)

    print(
        f"Found {len(reconstructible_verbs)} reconstructible candidates from derived roots."
    )

    # Validation Phase
    success_count = 0
    failures = []
    report_data = []

    for verb in reconstructible_verbs:
        generated_sets = engine.reconstruct_verb(verb)
        matches_all = True
        failed_forms = []
        ref = full_corpus_map.get(verb.definition)

        # Capture options for report
        options = generated_sets[0] if generated_sets else {fn: set() for fn in forms}

        if not generated_sets:
            matches_all = False
            failed_forms = ["Generation Failed"]
        else:
            for fn in forms:
                ref_word = ref.get(fn)
                if not ref_word:
                    continue
                if ref_word not in options.get(fn, set()):
                    matches_all = False
                    failed_forms.append(
                        f"{fn}: expected '{ref_word}', got {options.get(fn)}"
                    )

        if matches_all:
            success_count += 1
        else:
            failures.append(
                {
                    "definition": verb.definition,
                    "failed_forms": failed_forms,
                    "class": verb.class_name,
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

    print(f"Validation Success: {success_count}/{len(reconstructible_verbs)}")

    # Export Artifacts
    reports_dir = os.path.join(base_dir, "artifacts", "reports")
    os.makedirs(reports_dir, exist_ok=True)

    analysis_path = os.path.join(reports_dir, "consistency_analysis.csv")
    report_path = os.path.join(reports_dir, "reconstruction_report.csv")
    validation_path = os.path.join(reports_dir, "reconstruction_validation.json")

    # Save Consistency Analysis
    analysis_fields = [
        "definition",
        "assigned_class",
        "is_consistent",
        "mismatch_details",
    ] + [f"root_{fn}" for fn in forms]
    with open(analysis_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=analysis_fields)
        writer.writeheader()
        writer.writerows(consistency_analysis)

    # Save Matches Validated
    validated_matches_data = []
    for d in report_data:
        if d["success"]:
            validated_matches_data.append(
                {
                    "definition": d["definition"],
                    "class": d["class"],
                    "strictness": "strict",
                    "scope": "reconstructs",
                    # Include stem finals? We don't have them handy in report_data, but could pass through.
                    # For now simple schema is fine.
                }
            )

    if validated_matches_data:
        keys = ["definition", "class", "strictness", "scope"]
        with open(matches_output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(validated_matches_data)

    # Save Reconstruction Report
    with open(report_path, "w", encoding="utf-8", newline="") as f:
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

    with open(validation_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": f"{success_count}/{len(reconstructible_verbs)}",
                "failures": failures,
            },
            f,
            indent=4,
        )

    print(f"Artifacts saved to {reports_dir}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reconstruct verbs from roots.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    main(args.classes)
