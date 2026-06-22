import dataclasses
import json
import os
from collections import defaultdict
from typing import Any

from dictionary_pipeline.dictionary_forms import DictionaryVerb, Prediction
from dictionary_pipeline.json_utils import EnhancedJSONEncoderFactory
from dictionary_pipeline.phases.reconstruct_and_validate.artifacts import (
    load_validated_roots,
    save_validated_roots,
)
from dictionary_pipeline.phases.select_canonical_derivations.artifacts import (
    save_reconstructable_verbs,
    save_selection_snapshot,
)
from dictionary_pipeline.row_models import ValidatedRootRow


# handle special rule
def _remove_special_fields(d: dict[str, Any]) -> None:
    d.pop("original_data", None)
    d.pop("user_selected", None)


EnhancedJSONEncoder = EnhancedJSONEncoderFactory(
    dict_modification=_remove_special_fields
)


def sort_candidates(vl: list[DictionaryVerb]) -> list[DictionaryVerb]:
    """
    Sorts a list of DictionaryVerb candidates using deterministic heuristics:
    1. Filter to candidates matching the minimum h_grade_root length.
    2. Sort tie-breaks by: stem_type priority, h_grade_root, class_name, and raw dict representation.
    """
    if not vl:
        return []

    # 1. Find min length
    min_len = min(len(v.morphology.h_grade_root) for v in vl)

    # 2. Filter to candidates with min length
    candidates = [v for v in vl if len(v.morphology.h_grade_root) == min_len]

    # 3. Sort candidates to pick one deterministically
    # Priority: con > aspirated > s_stem > others
    def get_stem_priority(v: DictionaryVerb) -> int:
        st = v.original_data.get("stem_type", "")
        if st == "con":
            return 0
        if st == "aspirated":
            return 1
        if st == "s_stem":
            return 2
        return 3

    candidates.sort(
        key=lambda v: (
            get_stem_priority(v),
            v.morphology.h_grade_root,
            v.morphology.class_name,
            json.dumps(v.original_data, sort_keys=True),
        )
    )
    return candidates


def validate_shim_compatibility(
    base_verb: DictionaryVerb, shim_candidate: DictionaryVerb
) -> tuple[bool, list[str]]:
    """Validates whether a shim candidate (InfEventful) is compatible with a
    base FullStative verb for infinitive prediction.

    Rules (TASK-4.4):
      - h_grade_root: pre-matched via h_grade lookup; not re-checked here.
      - glottal_grade_root: must match unless *either* side is None (g_grade is
        sticky and is often absent for one or both derivations).
      - middle_voice: must match.
      - plural_pronouns: must match.
      - suffix class (class_name): NOT checked — shim uses its own eventive class.
      - post_root_morpheme: NOT checked.
      - set_type (set_a_b): NOT checked — shim may use Set A while stative uses Set B.

    Returns:
        (is_compatible, mismatches) where *mismatches* is a list of
        human-readable descriptions of fields that did not agree.
    """
    mismatches: list[str] = []

    base_g = base_verb.morphology.glottal_grade_root
    shim_g = shim_candidate.morphology.glottal_grade_root
    if base_g is not None and shim_g is not None and base_g != shim_g:
        mismatches.append(f"glottal_grade_root: base={base_g!r} vs shim={shim_g!r}")

    base_mv = base_verb.morphology.config.pron.middle_voice
    shim_mv = shim_candidate.morphology.config.pron.middle_voice
    if base_mv != shim_mv:
        mismatches.append(
            f"middle_voice: base={base_mv.value!r} vs shim={shim_mv.value!r}"
        )

    base_plural = base_verb.morphology.config.pron.plural_pronouns
    shim_plural = shim_candidate.morphology.config.pron.plural_pronouns
    if base_plural != shim_plural:
        mismatches.append(
            f"plural_pronouns: base={base_plural!r} vs shim={shim_plural!r}"
        )

    return len(mismatches) == 0, mismatches


def load_stative_shims() -> dict[str, dict[str, Any]]:
    """Load curated/stative_shims.csv in the multi-row candidate format.

    Returns a mapping of corpus_id -> curated override row for any corpus_id
    that has a user_selected = 'x' row. This dict is used by match_shim_config
    to honour user curation during the current pipeline run.

    If the CSV uses the legacy single-row-per-corpus-id format (no
    user_selected column), every row is treated as a curated override to
    preserve backward compatibility until the migration script is run.
    """
    import csv

    from dictionary_pipeline.paths import STATIVE_SHIMS_PATH

    if not os.path.exists(STATIVE_SHIMS_PATH):
        return {}

    overrides: dict[str, dict[str, Any]] = {}
    with open(STATIVE_SHIMS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        has_user_selected = "user_selected" in fieldnames

        for row in reader:
            c_id = row.get("corpus_id", "").strip()
            if not c_id:
                continue
            if has_user_selected:
                if row.get("user_selected") == "x":
                    overrides[c_id] = {
                        k: v
                        for k, v in row.items()
                        if k not in ("corpus_id", "user_selected", "pipeline_selected")
                    }
            else:
                # Legacy format: treat every row as an override
                overrides[c_id] = {
                    k: v
                    for k, v in row.items()
                    if k not in ("corpus_id", "user_selected", "pipeline_selected")
                }
    return overrides


def save_stative_shims(
    validated_verbs: list[DictionaryVerb],
    stative_corpus_ids: set[str],
    curated_overrides: dict[str, dict[str, Any]],
    deduped_verbs: list[DictionaryVerb] | None = None,
) -> None:
    """Write compatible INF_EVENTFUL shim candidates (grouped by corpus_id of
    their parent FULL_STATIVE verb) to curated/stative_shims.csv in the same
    multi-row format as validated_reconstructable_roots.csv.

    For each corpus_id:
    * INF_EVENTFUL candidates that pass validate_shim_compatibility() against
      the parent FULL_STATIVE verb are written as candidate rows.
    * pipeline_selected = 'x' is marked on the pipeline's chosen candidate
      (using sort_candidates on compatible candidates).
    * If a user override exists in curated_overrides, we validate it still
      matches a compatible candidate in the current run and mark
      user_selected = 'x'.  If the override can no longer be matched
      (config changed or failed compatibility), we bail (exit 1).

    Args:
        validated_verbs: all validated verbs from the current run (used to
            find INF_EVENTFUL candidates and the FULL_STATIVE base verb).
        stative_corpus_ids: corpus_ids of FULL_STATIVE verbs that need shims.
        curated_overrides: mapping corpus_id -> override config dict as
            returned by load_stative_shims().
        deduped_verbs: the canonical/deduped verbs from the current run.
    """
    from dictionary_pipeline.paths import STATIVE_SHIMS_PATH

    # Build lookups: h_grade_root -> list of INF_EVENTFUL/IMP_INF_EVENTFUL verbs,
    # and corpus_id -> FULL_STATIVE/STATIVE_NO_IMP verb object (for compatibility checks).
    inf_eventful_by_h_grade: dict[str, list[DictionaryVerb]] = defaultdict(list)
    for verb in validated_verbs:
        if verb.meta.prediction in (
            Prediction.INF_EVENTFUL,
            Prediction.IMP_INF_EVENTFUL,
        ):
            inf_eventful_by_h_grade[verb.morphology.h_grade_root].append(verb)

    stative_h_grade: dict[str, str] = {}
    stative_verbs: dict[str, DictionaryVerb] = {}
    source_verbs = deduped_verbs if deduped_verbs is not None else validated_verbs
    for verb in source_verbs:
        if verb.meta.prediction in (Prediction.FULL_STATIVE, Prediction.STATIVE_NO_IMP):
            c_id = str(verb.meta.corpus_id)
            if c_id in stative_corpus_ids:
                is_selected = (
                    getattr(verb, "user_selected", False)
                    or verb.original_data.get("pipeline_selected") == "x"
                )
                if is_selected or c_id not in stative_verbs:
                    stative_h_grade[c_id] = verb.morphology.h_grade_root
                    stative_verbs[c_id] = verb

    all_rows: list[dict[str, Any]] = []
    missing_overrides: list[str] = []

    for c_id in sorted(stative_corpus_ids, key=lambda x: int(x) if x.isdigit() else 0):
        h_grade = stative_h_grade.get(c_id)
        stative_verb = stative_verbs.get(c_id)
        if h_grade is None or stative_verb is None:
            continue
        shim_candidates = inf_eventful_by_h_grade.get(h_grade, [])
        if not shim_candidates:
            continue

        # Filter to candidates that pass compatibility rules (TASK-4.4).
        compatible_candidates = [
            c
            for c in shim_candidates
            if validate_shim_compatibility(stative_verb, c)[0]
        ]

        # Determine pipeline selection from compatible candidates only.
        sorted_shims = sort_candidates(compatible_candidates)
        pipeline_choice = sorted_shims[0] if sorted_shims else None

        # Determine user override match (must also be compatible).
        user_override = curated_overrides.get(c_id)
        user_chosen: DictionaryVerb | None = None
        if user_override:
            for candidate in compatible_candidates:
                if match_shim_config(candidate, user_override):
                    user_chosen = candidate
                    break
            if user_chosen is None:
                missing_overrides.append(c_id)

        # Build candidate rows for this corpus_id (compatible candidates only).
        for candidate in compatible_candidates:
            row = candidate.original_data.copy()
            # Ensure corpus_id is present
            row["corpus_id"] = c_id
            # Clear then set selection markers
            row["user_selected"] = ""
            row["pipeline_selected"] = ""
            if user_chosen is not None and candidate is user_chosen:
                row["user_selected"] = "x"
            if pipeline_choice is not None and candidate is pipeline_choice:
                row["pipeline_selected"] = "x"
            all_rows.append(row)

    if missing_overrides:
        print(
            "[ERROR] The following user-selected shim overrides no longer match any "
            f"compatible candidate in the current run: {missing_overrides}. "
            "The shim may have been invalidated by a change to the base verb's "
            "configuration (middle_voice, plural_pronouns, or glottal_grade_root)."
        )
        print("Aborting save to prevent data loss.")
        exit(1)

    if not all_rows:
        return

    # Write using ValidatedRootRow fieldnames for column-parity with validated roots
    fieldnames = ValidatedRootRow.get_fieldnames()
    # Ensure all expected columns are present in every row (fill missing with '')
    os.makedirs(os.path.dirname(STATIVE_SHIMS_PATH), exist_ok=True)
    import csv

    with open(STATIVE_SHIMS_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in all_rows:
            # Fill any missing fields with empty string
            writer.writerow({fn: row.get(fn, "") for fn in fieldnames})


def match_shim_config(verb: DictionaryVerb, config_row: dict[str, Any]) -> bool:
    def normalize_bool(v: Any) -> str:
        if v is None or v == "" or v is False or v == "False" or v == "None":
            return "False"
        if v is True or v == "True" or v == "x":
            return "True"
        return str(v)

    def normalize_str(v: Any) -> str:
        if v is None:
            return ""
        return str(v).strip()

    # Compare each field in config_row
    for k, expected in config_row.items():
        actual = verb.original_data.get(k)
        if k in (
            "metathesis_involved",
            "allow_h_metathesis",
            "middle_voice_h_metathesis",
            "plural",
            "ka_variant",
            "aki_1st",
            "uwa_v",
            "3rd_person_object",
            "translocutive",
            "translocutive_imp_only",
            "partitive",
            "distributive",
        ):
            if normalize_bool(actual) != normalize_bool(expected):
                return False
        else:
            if normalize_str(actual) != normalize_str(expected):
                return False
    return True


def dedupe_roots(
    validated_verbs: list[DictionaryVerb],
) -> tuple[list[DictionaryVerb], list[DictionaryVerb], list[dict[str, Any]]]:
    roots_by_corpus_id: dict[int | str, list[DictionaryVerb]] = {}
    for verb in validated_verbs:
        c_id = verb.corpus_id if verb.corpus_id is not None else "synthetic"
        if not c_id in roots_by_corpus_id:
            roots_by_corpus_id[c_id] = [verb]
        else:
            roots_by_corpus_id[c_id].append(verb)

    deduped_roots = []
    dropped = []
    snapshot_data = []

    # Sort corpus IDs for stable snapshot
    for c_id in sorted(
        roots_by_corpus_id.keys(), key=lambda x: int(x) if str(x).isdigit() else 0
    ):
        vl = roots_by_corpus_id[c_id]
        # Identify pipeline choice (shortest h_grade_root, tie-broken deterministically)
        candidates = sort_candidates(vl)

        # only accept full predictions for pipeline selected
        pipeline_choice = next(
            (
                c
                for c in candidates
                if c.meta.prediction
                in [
                    Prediction.FULL_EVENTFUL,
                    Prediction.FULL_STATIVE,
                    Prediction.STATIVE_NO_IMP,
                ]
            ),
            None,
        )
        if pipeline_choice:
            pipeline_choice.original_data["pipeline_selected"] = "x"

        # Create snapshot entry for this corpus_id
        options_snapshot = []
        for v in vl:
            v_dict = dataclasses.asdict(v)
            v_dict.pop("original_data", None)
            v_dict.pop("segmented_forms", None)
            v_dict.pop("derivations", None)
            v_dict.pop("shim", None)
            # Ensure user_selected is captured accurately in the dict
            v_dict["user_selected"] = getattr(v, "user_selected", False)
            v_dict["pipeline_selected"] = (
                v.original_data.get("pipeline_selected") == "x"
            )
            options_snapshot.append(v_dict)

        # Sort options for stability within the corpus entry
        options_snapshot.sort(
            key=lambda x: json.dumps(x, sort_keys=True, cls=EnhancedJSONEncoder)
        )

        snapshot_data.append(
            {
                "corpus_id": c_id,
                "definition": vl[0].definition,
                "options": options_snapshot,
            }
        )

        if len(vl) == 1:
            deduped_roots.append(vl[0])
            continue

        # Check for user override
        selected = [v for v in vl if getattr(v, "user_selected", False)]
        unique_selected_roots = {v.morphology.h_grade_root for v in selected}
        if len(unique_selected_roots) > 1:
            print(
                f"[ERROR] Multiple conflicting user_selected roots for corpus_id {c_id}: {list(unique_selected_roots)}"
            )
            exit(1)
        elif len(unique_selected_roots) == 1:
            deduped_roots.append(selected[0])
            continue

        # Default logic: use pipeline choice
        if pipeline_choice:
            deduped_roots.append(pipeline_choice)

    return deduped_roots, dropped, snapshot_data


def enrich_glottal_grades(verbs: list[DictionaryVerb]) -> None:
    """
    If an h_grade_root has exactly one attested glottal_grade_root across all
    verbs, apply that glottal_grade_root to any verbs sharing the same
    h_grade_root that are currently missing it.
    """
    # h_grade -> set of non-null glottal_grade_root values
    g_grades_by_h = defaultdict(set)
    for v in verbs:
        if v.morphology.glottal_grade_root is not None:
            g_grades_by_h[v.morphology.h_grade_root].add(
                v.morphology.glottal_grade_root
            )

    # h_grade -> single non-null g_grade if it's the only one
    enrichment_map = {
        h: next(iter(gs)) for h, gs in g_grades_by_h.items() if len(gs) == 1
    }

    enriched_count = 0
    for v in verbs:
        if (
            v.morphology.glottal_grade_root is None
            and v.morphology.h_grade_root in enrichment_map
        ):
            v.morphology.glottal_grade_root = enrichment_map[v.morphology.h_grade_root]
            enriched_count += 1

    if enriched_count > 0:
        print(f"[INFO] Enriched {enriched_count} verbs with inferred glottal grades.")


def select_canonical_derivations() -> None:
    """
    Select canonical derivations to represent verbs going forward. It is at this
    step that all over-generation is reduced and a single canonical derivation
    is picked for each corpus entry.

    Inputs:
    * VALIDATED_RECONSTRUCTABLE_ROOTS_PATH: all possible valid, reconstructable
    derivations for each lexical item as well as manual user-selected forms

    Outputs:
    * RECONSTRUCTABLE_VERBS_PATH: JSON of canonical derivations for each lexical item.
    """
    rows = load_validated_roots()
    if rows is None:
        print("Error: Validated roots not found.")
        return

    validated_verbs = []
    for row in rows:
        verb = DictionaryVerb.from_row(row)
        # Initialize pipeline_selected to empty string
        row["pipeline_selected"] = ""
        validated_verbs.append(verb)

    print(f"Loaded {len(validated_verbs)} validated verbs.")

    deduped_roots, dropped_items, snapshot_data = dedupe_roots(validated_verbs)
    print(
        f"Root-deduping: {len(deduped_roots)} unique roots, {len(dropped_items)} ambiguous items dropped"
    )

    save_selection_snapshot(snapshot_data, EnhancedJSONEncoder)

    enrich_glottal_grades(deduped_roots)

    # Resolve and attach stative shims
    stative_shims_map = load_stative_shims()

    # Group InfEventful and ImpInfEventful shims by h_grade_root across all validated verbs
    inf_eventful_by_h_grade = defaultdict(list)
    for verb in validated_verbs:
        if verb.meta.prediction in (
            Prediction.INF_EVENTFUL,
            Prediction.IMP_INF_EVENTFUL,
        ):
            inf_eventful_by_h_grade[verb.morphology.h_grade_root].append(verb)

    stative_corpus_ids: set[str] = set()
    for canonical_verb in deduped_roots:
        if canonical_verb.meta.prediction in (
            Prediction.FULL_STATIVE,
            Prediction.STATIVE_NO_IMP,
        ):
            c_id = canonical_verb.meta.corpus_id
            if not c_id:
                continue

            stative_corpus_ids.add(str(c_id))

            # Find candidate InfEventful shims matching this root
            shim_candidates = inf_eventful_by_h_grade.get(
                canonical_verb.morphology.h_grade_root, []
            )

            if not shim_candidates:
                continue

            # Clear user_selected/pipeline_selected for all InfEventful shims first
            for candidate in shim_candidates:
                candidate.original_data["user_selected"] = ""
                candidate.original_data["pipeline_selected"] = ""

            # Filter candidates to those that pass compatibility rules (TASK-4.4).
            compatible_candidates = [
                c
                for c in shim_candidates
                if validate_shim_compatibility(canonical_verb, c)[0]
            ]

            chosen_shim = None
            # Check user selection override in curated/stative_shims.csv
            user_override = stative_shims_map.get(str(c_id))
            if user_override:
                for candidate in compatible_candidates:
                    if match_shim_config(candidate, user_override):
                        chosen_shim = candidate
                        chosen_shim.original_data["user_selected"] = "x"
                        break

                if chosen_shim is None:
                    # The user-selected row no longer matches any compatible candidate.
                    # Determine whether it matched by config but failed compatibility,
                    # or disappeared entirely, to give an informative error.
                    config_matches = [
                        c
                        for c in shim_candidates
                        if match_shim_config(c, user_override)
                    ]
                    if config_matches:
                        _, mismatches = validate_shim_compatibility(
                            canonical_verb, config_matches[0]
                        )
                        print(
                            f"[ERROR] User-selected shim for corpus_id {c_id!r} is no "
                            f"longer compatible with the base verb. "
                            f"Mismatches: {mismatches}"
                        )
                    else:
                        print(
                            f"[ERROR] User-selected shim for corpus_id {c_id!r} no longer "
                            f"matches any candidate in the current run "
                            f"(derivation config changed)."
                        )
                    exit(1)

            if not chosen_shim:
                # Fall back to pipeline choice from compatible candidates only.
                sorted_shims = sort_candidates(compatible_candidates)
                if sorted_shims:
                    chosen_shim = sorted_shims[0]
                    chosen_shim.original_data["pipeline_selected"] = "x"

            if chosen_shim:
                canonical_verb.shim = chosen_shim

    # Save updated rows with pipeline_selected marks back to validated roots CSV
    save_validated_roots(rows)

    # Save shim candidates (all INF_EVENTFUL candidates for stative verbs)
    # with pipeline_selected and user_selected marked, validating curated overrides
    save_stative_shims(
        validated_verbs,
        stative_corpus_ids,
        stative_shims_map,
        deduped_verbs=deduped_roots,
    )

    # Save Fully Serialized Verbs
    save_reconstructable_verbs(deduped_roots, EnhancedJSONEncoder)


if __name__ == "__main__":
    select_canonical_derivations()
