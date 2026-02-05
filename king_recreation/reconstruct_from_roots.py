import csv
import dataclasses
import json
import os
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from king_recreation.h_alternation import possible_alternates, prevent_C_glottal_cluster
from king_recreation.morphemes.prepronominals import (
    PrePronominalConfig,
    apply_prepronominal,
)
from king_recreation.morphemes.pronominals import (
    PronominalConfig,
    attach_prefix,
    get_prefix_details,
    get_pronominal_set_name,
    use_glottal_grade,
)
from king_recreation.paths import (
    classes_expanded_path,
    consistency_analysis_path,
    corpus_path,
    derived_roots_path,
    reconstructable_verbs_path,
    reconstruction_failures_path,
    reconstruction_report_path,
    reconstruction_validation_path,
    reports_path,
    validated_matches_path,
)
from king_recreation.pattern_registry import PatternRegistry


@dataclass(frozen=True)
class VerbConfig:
    pre: PrePronominalConfig
    pron: PronominalConfig

    @staticmethod
    def from_row(stem_row: dict[str, str]) -> "VerbConfig":
        pre_config = PrePronominalConfig.from_row(stem_row)
        pron_config = PronominalConfig.from_row(stem_row)

        return VerbConfig(pre=pre_config, pron=pron_config)

    @staticmethod
    def from_dict(data: dict) -> "VerbConfig":
        return VerbConfig(
            pre=PrePronominalConfig.from_dict(data.get("pre", {})),
            pron=PronominalConfig.from_dict(data.get("pron", {})),
        )


@dataclass
class ReconstructibleVerb:
    definition: str
    h_grade_root: str
    glottal_grade_root: Optional[str]
    class_name: str
    config: VerbConfig
    corpus_id: Optional[int] = None
    entry_no: Optional[int] = None
    original_stems: Dict[str, str] = field(default_factory=dict)
    derivations: List["ReconstructibleVerb"] = field(default_factory=list)

    @staticmethod
    def from_dict(data: dict) -> "ReconstructibleVerb":
        clean_data = data.copy()
        if "config" in clean_data:
            clean_data["config"] = VerbConfig.from_dict(clean_data["config"])
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
        prefix, condition = get_prefix_details(set_name, config)

        stems_to_try = [(stem, False)]

        candidates = []
        for s, dropped in stems_to_try:
            res = attach_prefix(s, prefix, condition)
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

        return root

    def get_base_stems_for_form(self, verb: ReconstructibleVerb, form_name: str):
        class_info = self.classes.get(verb.class_name)
        if not class_info:
            return []

        glottal_grade = use_glottal_grade(form_name, verb.config.pron)
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
                set_name = get_pronominal_set_name(fn, verb.config.pron)
                if not set_name:
                    candidates = [stem]
                else:
                    candidates = self.generate_pronominal_forms(
                        stem, set_name, verb.config.pron
                    )

                for c in candidates:
                    layered_candidates.extend(
                        apply_prepronominal(c, verb.config.pre, fn)
                    )

                form_options[fn] = layered_candidates

        return [{fn: set(opts or []) for fn, opts in form_options.items()}]


def dedupe_roots(validated_verbs: list[ReconstructibleVerb]):
    roots_by_corpus_id: dict[str, list[ReconstructibleVerb]] = {}
    for verb in validated_verbs:
        c_id = verb.corpus_id
        if not c_id in roots_by_corpus_id:
            roots_by_corpus_id[c_id] = [verb]
        else:
            roots_by_corpus_id[c_id].append(verb)

    deduped_roots = []
    dropped = []

    for c_id, vl in roots_by_corpus_id.items():
        lowest_len = None
        lowest_v = None
        if len(vl) == 1:
            deduped_roots.append(vl[0])
        else:
            for v in vl:
                len_v = len(v.h_grade_root)
                if lowest_v is None or len_v < lowest_len:
                    lowest_len = len_v
                    lowest_v = v
                elif lowest_v == len_v:
                    print(
                        "[WARNING]",
                        v.class_name,
                        lowest_v.class_name,
                        "have same length root",
                    )
                    dropped.append(c_id)
                    break
            else:
                # print(
                #     "Lowest len root",
                #     lowest_v["definition"],
                #     lowest_v["h_grade_root"],
                #     lowest_v["class_name"],
                # )
                deduped_roots.append(lowest_v)

    return deduped_roots, dropped


def enrich_glottal_grades(verbs: List[ReconstructibleVerb]):
    """
    If an h_grade_root has exactly one attested glottal_grade_root across all verbs,
    apply that glottal_grade_root to any verbs sharing the same h_grade_root
    that are currently missing it.
    """
    # h_grade -> set of non-null glottal_grade_root values
    g_grades_by_h = defaultdict(set)
    for v in verbs:
        if v.glottal_grade_root is not None:
            g_grades_by_h[v.h_grade_root].add(v.glottal_grade_root)

    # h_grade -> single non-null g_grade if it's the only one
    enrichment_map = {
        h: next(iter(gs)) for h, gs in g_grades_by_h.items() if len(gs) == 1
    }

    enriched_count = 0
    for v in verbs:
        if v.glottal_grade_root is None and v.h_grade_root in enrichment_map:
            v.glottal_grade_root = enrichment_map[v.h_grade_root]
            enriched_count += 1

    if enriched_count > 0:
        print(f"[INFO] Enriched {enriched_count} verbs with inferred glottal grades.")


def main(classes_path=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

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
            full_corpus_map[row["corpus_id"]] = row

    reconstructible_verbs: list[ReconstructibleVerb] = []
    consistency_analysis = []
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]

    for stem_row in derived_roots:
        definition = stem_row["definition"]
        cls_name = stem_row["class"]

        # In derived_roots context, the columns like 'present', 'present_1sg' are already stripped roots
        h_root = stem_row.get("consensus_root")
        if h_root is None:
            # Fallback if consensus_root not written (e.g. absent from row? derived_stems writes it)
            h_root = stem_row.get("present")

        config = VerbConfig.from_row(stem_row)

        # Glottal root: If 1sg is glottal (Set A), use the derived 1sg root.
        glottal_root = None
        if use_glottal_grade("present_1sg", config.pron):
            ref_word = full_corpus_map.get(stem_row.get("corpus_id"), {}).get(
                "present_1sg"
            )
            if ref_word:
                glottal_root = stem_row.get("present_1sg")

        # Optional: We could re-verify consistency here, but derive_stems checks it.
        # We assume if it's in derived_roots, it passed basic consistency.

        verb = ReconstructibleVerb(
            definition=definition,
            h_grade_root=h_root,
            glottal_grade_root=glottal_root,
            class_name=cls_name,
            config=config,
            corpus_id=int(stem_row["corpus_id"]) if "corpus_id" in stem_row else None,
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
    validated_verbs: List[ReconstructibleVerb] = []

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

    # Dedupe roots when one parse gives a strictly shorter root than all others
    deduped_roots, dropped_items = dedupe_roots(validated_verbs)

    print(
        f"Root-deduping: {len(deduped_roots)} unique roots, {len(dropped_items)} ambiguous items dropped"
    )

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

    # Enrich missing glottal grades before final serialization
    enrich_glottal_grades(deduped_roots)

    # Save Fully Serialized Verbs
    with open(reconstructable_verbs_path, "w", encoding="utf-8") as f:
        json.dump(deduped_roots, f, cls=EnhancedJSONEncoder, indent=4)

    # Save classes used for reconstructions
    with open(classes_expanded_path, "w", encoding="utf-8") as f:
        json.dump(engine.classes, f, cls=EnhancedJSONEncoder, indent=4)

    print(f"Artifacts saved to {reports_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Reconstruct verbs from roots.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    main(args.classes)
