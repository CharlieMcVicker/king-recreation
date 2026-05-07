import dataclasses
import json
from collections import defaultdict

from king_recreation.dictionary_forms import build_wordspec
from king_recreation.morphemes.prefixes import PrefixConfig
from king_recreation.morphemes.prefixes.pronominals import use_glottal_grade
from king_recreation.phases.reconstruct_and_validate.artifacts import (
    load_validated_roots,
    save_validated_roots,
)
from king_recreation.phases.select_canonical_derivations.artifacts import (
    save_reconstructable_verbs,
    save_selection_snapshot,
)
from king_recreation.reconstruction import ReconstructableVerb
from king_recreation.utils import EnhancedJSONEncoderFactory

# handle special rule
EnhancedJSONEncoder = EnhancedJSONEncoderFactory(
    dict_modification=lambda d: (
        d.pop("original_data", None),
        d.pop("user_selected", None),
    )
)


def dedupe_roots(
    validated_verbs: list[ReconstructableVerb],
) -> tuple[list[ReconstructableVerb], list[ReconstructableVerb], list[dict]]:
    roots_by_corpus_id: dict[str, list[ReconstructableVerb]] = {}
    for verb in validated_verbs:
        c_id = verb.corpus_id
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

        # 1. Find min length
        min_len = min(len(v.h_grade_root) for v in vl)

        # 2. Filter to candidates with min length
        candidates = [v for v in vl if len(v.h_grade_root) == min_len]

        # 3. Sort candidates to pick one deterministically
        # Priority: con > aspirated > s_stem > others
        def get_stem_priority(v: ReconstructableVerb) -> int:
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
                v.h_grade_root,
                v.class_name,
                json.dumps(v.original_data, sort_keys=True),
            )
        )

        pipeline_choice = candidates[0]
        pipeline_choice.original_data["pipeline_selected"] = "x"

        # Create snapshot entry for this corpus_id
        options_snapshot = []
        for v in vl:
            v_dict = dataclasses.asdict(v)
            v_dict.pop("original_data", None)
            v_dict.pop("segmented_forms", None)
            v_dict.pop("derivations", None)
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
        unique_selected_roots = {v.h_grade_root for v in selected}
        if len(unique_selected_roots) > 1:
            print(
                f"[ERROR] Multiple conflicting user_selected roots for corpus_id {c_id}: {list(unique_selected_roots)}"
            )
            exit(1)
        elif len(unique_selected_roots) == 1:
            deduped_roots.append(selected[0])
            continue

        # Default logic: use pipeline choice
        deduped_roots.append(pipeline_choice)

    return deduped_roots, dropped, snapshot_data


def enrich_glottal_grades(verbs: list[ReconstructableVerb]) -> None:
    """
    If an h_grade_root has exactly one attested glottal_grade_root across all
    verbs, apply that glottal_grade_root to any verbs sharing the same
    h_grade_root that are currently missing it.
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
        # Reconstruct ReconstructableVerb object
        config = PrefixConfig.from_row(row)

        definition = row["definition"]
        cls_name = row["class"]
        post_root_morpheme = row.get("post_root_morpheme")
        post_root_morpheme = post_root_morpheme if post_root_morpheme else None

        h_root = row["h_grade"]

        glottal_root = None
        spec_1sg = build_wordspec("present_1sg", config.pron, config.stative)
        if use_glottal_grade(spec_1sg.person, spec_1sg.number, spec_1sg.pronominal_set):
            glottal_root = row["g_grade"]
            if glottal_root == "" and not h_root == "":
                glottal_root = None

        corpus_id = int(row["corpus_id"]) if "corpus_id" in row else None
        entry_no = (
            int(row["entry_no"]) if "entry_no" in row and row["entry_no"] else None
        )

        verb = ReconstructableVerb(
            definition=definition,
            h_grade_root=h_root,
            glottal_grade_root=glottal_root,
            class_name=cls_name,
            post_root_morpheme=post_root_morpheme,
            config=config,
            corpus_id=corpus_id,
            entry_no=entry_no,
            original_data=row,  # Keep it if we want to pass it further, though JSON serialization dumps fields
        )
        # Monkey-patch or attach user_selected for use in dedupe
        verb.user_selected = row.get("user_selected") == "x"
        # Deserialize segmented_forms
        if "segmented_forms" in row and row["segmented_forms"]:
            try:
                verb.segmented_forms = json.loads(row["segmented_forms"])
            except json.JSONDecodeError:
                verb.segmented_forms = {}

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

    # Save updated rows with pipeline_selected marks back to CSV
    save_validated_roots(rows)

    # Save Fully Serialized Verbs
    save_reconstructable_verbs(deduped_roots, EnhancedJSONEncoder)


if __name__ == "__main__":
    select_canonical_derivations()
