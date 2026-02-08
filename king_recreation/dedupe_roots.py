import csv
import dataclasses
import json
import os
from collections import defaultdict
from enum import Enum
from typing import List

from king_recreation.morphemes.prefixes import PrefixConfig
from king_recreation.morphemes.prefixes.pronominals import use_glottal_grade
from king_recreation.paths import (
    reconstructable_verbs_path,
    validated_reconstructable_roots_path,
)
from king_recreation.reconstruct_from_roots import ReconstructibleVerb


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            d = dataclasses.asdict(o)
            d.pop("original_data", None)
            return d
        if isinstance(o, Enum):
            return o.value
        return super().default(o)


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

            # Default logic
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


def main():
    if not os.path.exists(validated_reconstructable_roots_path):
        print(f"Error: {validated_reconstructable_roots_path} not found.")
        return

    validated_verbs = []
    with open(validated_reconstructable_roots_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Reconstruct ReconstructibleVerb object
            config = PrefixConfig.from_row(row)

            # Logic to reconstruct h_root/glottal_root/post_root if not directly in row?
            # The row is the original derived root row.

            definition = row["definition"]
            cls_name = row["class"]
            post_root_morpheme = row.get("post_root_morpheme")
            post_root_morpheme = post_root_morpheme if post_root_morpheme else None

            h_root = row["h_grade"]

            # Re-apply glottal logic or just take it from row?
            # In reconstruct_from_roots, glottal_root was derived:
            # if use_glottal_grade("present_1sg", config.pron): glottal_root = stem_row["g_grade"]...
            # We should replicate this logic to be safe, or assume the row has what we need?
            # actually row has "g_grade".

            glottal_root = None
            if use_glottal_grade("present_1sg", config.pron, config.stative):
                glottal_root = row["g_grade"]
                if glottal_root == "" and not h_root == "":
                    glottal_root = None

            corpus_id = int(row["corpus_id"]) if "corpus_id" in row else None
            entry_no = (
                int(row["entry_no"]) if "entry_no" in row and row["entry_no"] else None
            )

            verb = ReconstructibleVerb(
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
            validated_verbs.append(verb)

    print(f"Loaded {len(validated_verbs)} validated verbs.")

    deduped_roots, dropped_items = dedupe_roots(validated_verbs)
    print(
        f"Root-deduping: {len(deduped_roots)} unique roots, {len(dropped_items)} ambiguous items dropped"
    )

    enrich_glottal_grades(deduped_roots)

    # Save Fully Serialized Verbs
    with open(reconstructable_verbs_path, "w", encoding="utf-8") as f:
        json.dump(deduped_roots, f, cls=EnhancedJSONEncoder, indent=4)

    print(f"Artifacts saved to {reconstructable_verbs_path}")


if __name__ == "__main__":
    main()
