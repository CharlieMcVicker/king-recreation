import csv
import dataclasses
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from king_recreation.h_alternation import possible_alternates, prevent_C_glottal_cluster
from king_recreation.morphemes.aspect.pattern_registry import PatternRegistry
from king_recreation.morphemes.post_root_morphemes import PostRootMorphemeRegistry
from king_recreation.morphemes.prefixes import PrefixConfig
from king_recreation.morphemes.prefixes.pronominals import (
    PronominalConfig,
    get_prefix_details,
    get_pronominal_set_name,
    use_glottal_grade,
)
from king_recreation.paths import (
    classes_expanded_path,
    consistency_analysis_path,
    corpus_no_pre_no_asp_path,
    corpus_path,
    reconstructable_verbs_path,
    reconstruction_failures_path,
    reconstruction_report_path,
    reconstruction_validation_path,
    reports_path,
    validated_matches_path,
    validated_reconstructable_roots_path,
)


@dataclass
class ReconstructibleVerb:
    definition: str
    h_grade_root: str
    glottal_grade_root: Optional[str]
    post_root_morpheme: Optional[str]
    class_name: str
    config: PrefixConfig
    corpus_id: Optional[int] = None
    entry_no: Optional[int] = None
    derivations: List["ReconstructibleVerb"] = field(default_factory=list)
    original_data: dict = field(
        default_factory=dict, repr=False, hash=False, compare=False
    )

    # TODO: IS THIS DEAD?
    @staticmethod
    def from_dict(data: dict) -> "ReconstructibleVerb":
        clean_data = data.copy()
        if "config" in clean_data:
            clean_data["config"] = PrefixConfig.from_dict(clean_data["config"])
        if "post_root_morpheme" in clean_data:
            val = clean_data["post_root_morpheme"]
            # turn "" to None
            clean_data["post_root_morpheme"] = val if val else None
        return ReconstructibleVerb(**clean_data)


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


class ReconstructionEngine:
    def __init__(self, classes_path: Optional[str]):
        registry = PatternRegistry.get_instance()
        registry.load_from_csv(classes_path)
        # Create the name -> pattern map expected by reconstruct_verb
        self.classes = {p.name: p for p in registry.expanded_patterns}

    # _load_classes_raw removed as it is replaced by ClassPatterns.from_csv

    def generate_pronominal_forms(
        self, stem: str, set_name: str, config: PronominalConfig
    ) -> List[str]:
        prefix = get_prefix_details(set_name, config)

        stems_to_try = [(stem, False)]

        candidates = []
        for stem, dropped in stems_to_try:
            res = prefix.attach(stem)
            if res:
                candidates.append(res)
        return candidates

    def root_for_form(
        self, verb: ReconstructibleVerb, glottal_grade: bool
    ) -> Optional[str]:
        # Determine Grade
        # Default: h-grade
        root = verb.glottal_grade_root if glottal_grade else verb.h_grade_root

        if glottal_grade and root is None:
            # Missing required root for this form
            return None

        if root is None:
            return None

        # apply middle voice
        root = verb.config.pron.middle_voice.apply(root, glottal_grade)

        if verb.post_root_morpheme:
            reg = PostRootMorphemeRegistry.get_instance()
            root = root + reg.morphemes_by_name[verb.post_root_morpheme].form

        return root

    def get_base_stems_for_form(self, verb: ReconstructibleVerb, form_name: str):
        class_info = self.classes.get(verb.class_name)
        if not class_info:
            return []

        glottal_grade = use_glottal_grade(
            form_name, verb.config.pron, verb.config.stative
        )
        root = self.root_for_form(verb, glottal_grade)

        if root is None:
            return None

        # apply aspect suffix

        ending_pattern = class_info.get(form_name, "")
        if form_name == "present_1sg" and not ending_pattern:
            ending_pattern = class_info.present

        # just phonological content of ending
        literal_ending = ending_pattern.replace("*", "").replace("@", "")

        # truncate if pattern calls for it
        if "*" in ending_pattern:
            if len(root) >= 1:
                root = root[:-1]
        elif "@" in ending_pattern:
            if len(root) >= 2:
                root = root[:-2]

        # if we need to /h/ alternate but there wasnt an h in the h grade root
        # we need to try to drop it from the ending
        if glottal_grade and not "h" in verb.h_grade_root:
            return [
                prevent_C_glottal_cluster(root + literal_ending)
                for literal_ending in possible_alternates(
                    literal_ending, fix_clusters=False
                )
            ]
        else:
            return [root + literal_ending]

    def get_base_stems(self, verb: ReconstructibleVerb):
        base_stems = {}

        for form_name in [
            "present",
            "present_1sg",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]:
            stems = self.get_base_stems_for_form(verb, form_name)
            if stems:
                base_stems[form_name] = stems

        return base_stems

    def reconstruct_verb(self, verb: ReconstructibleVerb) -> List[Dict[str, str]]:
        base_stems = self.get_base_stems(verb)

        form_options = {}
        for fn, stems in base_stems.items():
            # Apply Prepronominals
            layered_candidates = []

            for stem in stems if isinstance(stems, list) else [stems]:
                set_name = get_pronominal_set_name(
                    fn, verb.config.pron, verb.config.stative
                )
                if not set_name:
                    raise Exception("WAHH")
                    candidates = [stem]
                else:
                    candidates = self.generate_pronominal_forms(
                        stem, set_name, verb.config.pron
                    )

                for c in candidates:
                    layered_candidates.extend(verb.config.apply_prepronominals(c, fn))

                form_options[fn] = layered_candidates

        return [{fn: set(opts or []) for fn, opts in form_options.items()}]


def main(classes_path=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    engine = ReconstructionEngine(classes_path)

    # Load Derived Roots
    derived_roots = []
    if os.path.exists(corpus_no_pre_no_asp_path):
        with open(corpus_no_pre_no_asp_path, "r", encoding="utf-8") as f:
            derived_roots = list(csv.DictReader(f))
    else:
        print(f"Error: {corpus_no_pre_no_asp_path} not found.")
        return

    # Load existing validated roots to persist user selections
    user_selected_rows = []
    if os.path.exists(validated_reconstructable_roots_path):
        with open(validated_reconstructable_roots_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "user_selected" in reader.fieldnames:
                for row in reader:
                    if row.get("user_selected") == "x":
                        user_selected_rows.append(row)

    print(f"Loaded {len(user_selected_rows)} user-selected rows for persistence.")

    # Load raw Corpus
    full_corpus_map = {}
    with open(corpus_path, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            full_corpus_map[row["corpus_id"]] = row

    reconstructible_verbs: list[ReconstructibleVerb] = []
    consistency_analysis = []
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]

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

        verb = ReconstructibleVerb(
            definition=definition,
            h_grade_root=h_root,
            glottal_grade_root=glottal_root,
            class_name=cls_name,
            post_root_morpheme=post_root_morpheme,
            config=config,
            corpus_id=int(stem_row["corpus_id"]) if "corpus_id" in stem_row else None,
            original_data=stem_row,
        )
        reconstructible_verbs.append(verb)

    print(
        f"Found {len(reconstructible_verbs)} reconstructible candidates from derived roots."
    )

    # Validation Phase
    success_count = 0
    failures = []
    report_data = []
    validated_verbs: List[ReconstructibleVerb] = []
    validated_rows: List[dict] = []

    for verb in reconstructible_verbs:
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
                        f"{fn}: expected '{ref_word}', got {sorted(list(options.get(fn, set())))}"
                    )

        if matches_all:
            success_count += 1
            validated_verbs.append(verb)
            # Inject entry_no into original_data so it persists to the CSV
            if verb.entry_no is not None:
                verb.original_data["entry_no"] = verb.entry_no

            # Check if this matches a user selected row
            # We match on all fields except user_selected and entry_no to be safe,
            # or simply use the fact that original_data might match if it hasn't changed.
            # However, ReconstructibleVerb reconstructs data which might differ slightly if logic changes.
            # But the requirement is: "fail when rewriting if we would drop a row that was user marked"
            # This implies the row must be EXACTLY valid as per current logic.
            # So we check if the currently generated `verb.original_data` (augmented with keys)
            # matches the critical fields of a saved user_selection.

            # Let's match on specific identity fields to be robust:
            # corpus_id, definition, class, h_grade, g_grade, post_root_morpheme

            def get_identity_key(r):
                return (
                    str(r.get("corpus_id", "")),
                    r.get("definition", ""),
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
                    r.get("long_start", ""),
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

    print(f"Validation Success: {success_count}/{len(reconstructible_verbs)}")

    # Save Consistency Analysis
    analysis_fields = [
        "definition",
        "assigned_class",
        "is_consistent",
        "mismatch_details",
    ] + [f"root_{fn}" for fn in forms]
    with open(consistency_analysis_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=analysis_fields)
        writer.writeheader()
        writer.writerows(consistency_analysis)

    # Save Matches Validated
    validated_matches_data = []
    for d, verb in zip(report_data, reconstructible_verbs):
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
        with open(validated_matches_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(validated_matches_data)

    # Save Reconstruction Report
    with open(reconstruction_report_path, "w", encoding="utf-8", newline="") as f:
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

    with open(reconstruction_validation_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "summary": f"{success_count}/{len(reconstructible_verbs)}",
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
                r.get("definition", ""),
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
                r.get("long_start", ""),
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
            "long_start",
            "aki_1st",
            "uwa_v",
            "3rd_person_object",
            "translocutive",
            "translocutive_imp_only",
            "partitive",
            "distributive",
            "distributive_fut_prog",
        ]

        # Ensure standard order of important columns if possible, but taking from first row is standard here
        # Make sure optional columns are present
        for col in ["entry_no", "user_selected"]:
            if col not in fieldnames and col in all_keys:
                fieldnames.append(col)

        with open(
            validated_reconstructable_roots_path, "w", encoding="utf-8", newline=""
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

    with open(reconstruction_failures_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["corpus_id", "definition", "class", "mismatch_details"],
        )
        writer.writeheader()
        writer.writerows(failures_csv_data)

    print(f"Artifacts saved to {reports_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reconstruct verbs from roots.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    main(args.classes)
