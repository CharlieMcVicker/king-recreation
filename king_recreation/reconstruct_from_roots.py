from king_recreation.phonology_data import grades_are_compatible
import os
import csv
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from king_recreation.classify_verbs import get_matches_for_verb
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
    def __init__(self, king_classes_path: str):
        self._classes_raw = self._load_king_classes_raw(king_classes_path)
        self.king_classes = {row["class"]: row for row in self._classes_raw}

    def _load_king_classes_raw(self, path: str) -> List[Dict[str, str]]:
        classes = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                classes.append(row)
        return classes

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
        class_info = self.king_classes.get(verb.class_name)
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
                ending_pattern = class_info.get("present", "")

            literal_ending = ending_pattern.replace("*", "").replace("@", "")

            # Determine Grade
            # Default: h-grade
            glottal_grade_form = use_glottal_grade(form_name, verb.config.pron)
            root_to_use = (
                verb.glottal_grade_root if glottal_grade_form else verb.h_grade_root
            )

            if glottal_grade_form and not root_to_use:
                # Missing required root for this form
                continue

            if not root_to_use:
                continue

            modified_root = root_to_use
            if "*" in ending_pattern:
                if len(modified_root) >= 1:
                    modified_root = modified_root[:-1]
            elif "@" in ending_pattern:
                if len(modified_root) >= 2:
                    modified_root = modified_root[:-2]

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
    stem_corpus_path = os.path.join(base_dir, "artifacts", "data", "stem_corpus.csv")
    corpus_path = os.path.join(base_dir, "artifacts", "data", "corpus.csv")
    if classes_path is None:
        king_classes_path = os.path.join(base_dir, "data", "king_classes.csv")
    else:
        king_classes_path = classes_path
    matches_path = os.path.join(base_dir, "artifacts", "data", "matches.csv")

    engine = ReconstructionEngine(king_classes_path)

    # Load Stem Corpus
    stem_corpus_map = {}
    with open(stem_corpus_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            stem_corpus_map[row["definition"]] = row

    # Load raw Corpus
    full_corpus_map = {}
    with open(corpus_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            full_corpus_map[row["definition"]] = row

    # Load Matches
    matches = []
    if os.path.exists(matches_path):
        with open(matches_path, "r", encoding="utf-8") as f:
            matches = list(csv.DictReader(f))

    reconstructible_verbs: list[ReconstructibleVerb] = []
    consistency_analysis = []
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]

    # Filter for 'reconstructs' scope matches (strictly)
    reconstruct_matches = [
        m
        for m in matches
        if m["scope"] == "reconstructs" and m["strictness"] == "strict"
    ]

    # Updated Loop: Iterate all stem_corpus entries that are fully populated (roughly)
    # Actually, we should stick to iterating matches that were deemed 'reconstructs' -> 'strict' to keep the pipeline stable,
    # OR better yet, iterate all stem_corpus rows and see if they can form a ReconstructibleVerb.
    # The original code filtered by matches.csv ('reconstructs').
    # Let's keep that filter for now to avoid processing garbage, but we must update the consistency logic.

    for match in reconstruct_matches:
        definition = match["definition"]
        cls_name = match["class"]
        stem_row = stem_corpus_map.get(definition)
        if not stem_row:
            continue

        class_info = engine.king_classes[cls_name]

        # 1. Extract Roots
        # h-grade: derived from 'present' (3rd person)
        root_h_candidate = get_root_candidate(
            stem_row.get("present", ""), class_info.get("present", "")
        )

        # glottal-grade: derived from 'present_1sg'
        # Default to 'present' pattern if 'present_1sg' not specified in class
        pat_1sg = class_info.get("present_1sg") or class_info.get("present", "")
        root_glottal_candidate = get_root_candidate(
            stem_row.get("present_1sg", ""), pat_1sg
        )

        # Determine strictness of glottal grade availability
        config = VerbConfig.from_row(stem_row)

        # Glottal grade is needed/visible if:
        # 1. Set A (1sg is Set A)
        # 2. To 3rd (1sg is 1->3)
        # Note: Set B 1sg uses aki- (h-grade equivalent behavior in terms of root? No, Set B is h-grade usually).
        # Spec: "h if set B, glottal if Set A or to third person" for present_1sg.

        h_root = root_h_candidate
        glottal_root = (
            root_glottal_candidate
            if use_glottal_grade("present_1sg", config.pron)
            else None
        )

        # If we expect a glottal root (Set A) but don't have one (present_1sg missing), we might have an issue.
        # But stick to data availability.

        # 2. Check Consistency (H-dropping check)
        is_consistent = True
        mismatch_details = []

        if not h_root:
            is_consistent = False
            mismatch_details.append("Missing h-grade root (present)")

        if is_consistent and glottal_root:
            if not grades_are_compatible(h=h_root, glottal=glottal_root):
                # "Expect some forms to have diverging... which fail this check." -> But for now let's mark inconsistent?
                # User said: "flag forms for which derivation is possible but... dont match".
                # User also said: "make it blocking eventually." -> "flag mismatches in report"
                # Let's mark is_consistent = False for the REPORT, but maybe still allow reconstruction if roots are present?
                # Spec says: "Forms will then be checked against the matching grade root".
                # If we mark it inconsistent, does it stop reconstruction?
                # Previous code: `if consistent: ... reconstructible_verbs.append(...)`
                # So yes, it blocks reconstruction in this pipeline.

                # Check for "vacuous" match?
                # If h_root has no h? "ali" -> "ali" == "ali".
                # If mismatch:
                is_consistent = False
                mismatch_details.append(
                    f"Grade Mismatch: h-grade '{h_root}' != glottal-grade '{glottal_root}'"
                )

        analysis_row = {
            "definition": definition,
            "assigned_class": cls_name,
            "is_consistent": is_consistent,
            "mismatch_details": "; ".join(mismatch_details),
        }
        for fn in forms:
            analysis_row[f"root_{fn}"] = (
                get_root_candidate(stem_row.get(fn, ""), class_info.get(fn, "")) or ""
            )
        consistency_analysis.append(analysis_row)

        if is_consistent:
            from king_recreation.phonology_data import StemType, MetathesisStrategy

            verb = ReconstructibleVerb(
                definition=definition,
                h_grade_root=h_root,
                glottal_grade_root=glottal_root,
                class_name=cls_name,
                config=VerbConfig.from_row(stem_row),
                original_stems={fn: stem_row[fn] for fn in forms},
            )
            reconstructible_verbs.append(verb)

    print(f"Found {len(reconstructible_verbs)} reconstructible verbs.")

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
