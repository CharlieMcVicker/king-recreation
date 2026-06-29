import csv
import os
import sys

# Ensure repository root is in sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from dictionary_pipeline.phases.select_canonical_derivations.artifacts import (
    load_reconstructable_verbs,
)
from morphology.reconstruction import desegment


def main():
    verbs = load_reconstructable_verbs()
    print(f"Loaded {len(verbs)} reconstructable verbs.")

    # Collect all unique verb objects (including nested derivations and shims)
    all_verbs = []
    seen_ids = set()

    def collect(v):
        if not v:
            return
        if id(v) in seen_ids:
            return
        seen_ids.add(id(v))
        all_verbs.append(v)
        if hasattr(v, "derivations") and v.derivations:
            for deriv in v.derivations:
                collect(deriv)
        if hasattr(v, "shim") and v.shim:
            collect(v.shim)

    for verb in verbs:
        collect(verb)

    print(f"Collected {len(all_verbs)} verbs (including nested ones).")

    # Extract row entries
    rows = []
    seen_rows = set()

    for v in all_verbs:
        corpus_id = v.meta.corpus_id if (v.meta and v.meta.corpus_id) else ""
        if not corpus_id:
            continue

        if not hasattr(v, "segmented_forms") or not v.segmented_forms:
            continue

        for form_name, segmented in v.segmented_forms.items():
            if not segmented:
                continue
            surface = desegment(segmented)
            row_key = (corpus_id, form_name, surface, segmented)
            if row_key not in seen_rows:
                seen_rows.add(row_key)
                rows.append(
                    {
                        "corpus_id": corpus_id,
                        "form_name": form_name,
                        "surface": surface,
                        "segmented": segmented,
                    }
                )

    # Sort the rows for deterministic output (for easy diffing)
    def sort_key(r):
        cid = r["corpus_id"]
        try:
            cid_val = int(cid)
        except ValueError:
            cid_val = float("inf")
        return (cid_val, cid, r["form_name"])

    rows.sort(key=sort_key)

    output_path = os.path.join(REPO_ROOT, "artifacts", "verb_form_segmentations.csv")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["corpus_id", "form_name", "surface", "segmented"]
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Successfully wrote {len(rows)} entries to {output_path}")


if __name__ == "__main__":
    main()
