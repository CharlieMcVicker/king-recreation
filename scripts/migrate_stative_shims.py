"""One-time migration: stative_shims.csv → multi-row candidate format.

The legacy format stored a single configuration row per corpus_id, encoding the
user's chosen shim as a flat dict of config keys. The new format mirrors
curated/validated_reconstructable_roots.csv: all INF_EVENTFUL candidate rows for
each stative verb are stored with user_selected / pipeline_selected markers.

Usage (from repo root):
    source .venv/bin/activate
    python -m scripts.migrate_stative_shims

The script reads the current stative_shims.csv, looks up matching INF_EVENTFUL
candidate rows in validated_reconstructable_roots.csv, and rewrites stative_shims.csv
in the new multi-row format with user_selected = 'x' on the matched row.

If any existing curated entry cannot be matched in validated_reconstructable_roots.csv,
the script exits with an error — no data is written — so you can investigate before
proceeding.
"""

import csv
import os
import sys

# Allow running as `python -m scripts.migrate_stative_shims` from repo root
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIVE_SHIMS_PATH = os.path.join(REPO_ROOT, "curated", "stative_shims.csv")
VALIDATED_ROOTS_PATH = os.path.join(
    REPO_ROOT, "curated", "validated_reconstructable_roots.csv"
)


def _normalize_bool(v: object) -> str:
    if v is None or v == "" or v is False or v == "False" or v == "None":
        return "False"
    if v is True or v == "True" or v == "x":
        return "True"
    return str(v)


def _normalize_str(v: object) -> str:
    return "" if v is None else str(v).strip()


# Fields used by match_shim_config to compare config rows
BOOL_FIELDS = {
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
}


def _matches(candidate_row: dict, config_row: dict) -> bool:
    """Return True if all keys in config_row match the candidate_row."""
    for k, expected in config_row.items():
        actual = candidate_row.get(k)
        if k in BOOL_FIELDS:
            if _normalize_bool(actual) != _normalize_bool(expected):
                return False
        else:
            if _normalize_str(actual) != _normalize_str(expected):
                return False
    return True


def main() -> None:
    # ── 1. Load legacy stative_shims.csv ──────────────────────────────────────
    if not os.path.exists(STATIVE_SHIMS_PATH):
        print("[INFO] curated/stative_shims.csv not found — nothing to migrate.")
        return

    with open(STATIVE_SHIMS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        legacy_rows = list(reader)
        legacy_fieldnames = list(reader.fieldnames or [])

    if not legacy_rows:
        print("[INFO] stative_shims.csv is empty — nothing to migrate.")
        return

    # Detect if already migrated (has user_selected column)
    if "user_selected" in legacy_fieldnames:
        print(
            "[INFO] stative_shims.csv already has a 'user_selected' column — "
            "looks like it's already in the new format. Nothing to do."
        )
        return

    print(f"[INFO] Found {len(legacy_rows)} legacy shim row(s) to migrate.")

    # Build legacy overrides: corpus_id -> config dict (everything except corpus_id)
    legacy_overrides: dict[str, dict] = {}
    for row in legacy_rows:
        c_id = str(row.get("corpus_id", "")).strip()
        if c_id:
            legacy_overrides[c_id] = {k: v for k, v in row.items() if k != "corpus_id"}

    # ── 2. Load validated_reconstructable_roots.csv ───────────────────────────
    if not os.path.exists(VALIDATED_ROOTS_PATH):
        print(
            "[ERROR] curated/validated_reconstructable_roots.csv not found. "
            "Run the reconstruct_and_validate pipeline phase first."
        )
        sys.exit(1)

    with open(VALIDATED_ROOTS_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        all_root_rows = list(reader)
        new_fieldnames = list(reader.fieldnames or [])

    # Index INF_EVENTFUL rows by corpus_id
    inf_eventful_by_cid: dict[str, list[dict]] = {}
    for row in all_root_rows:
        if row.get("prediction") == "InfEventful":
            c_id = str(row.get("corpus_id", "")).strip()
            if c_id:
                inf_eventful_by_cid.setdefault(c_id, []).append(row)

    # ── 3. Match each legacy override against INF_EVENTFUL candidates ─────────
    unmatched: list[str] = []
    matched: dict[str, dict] = {}  # corpus_id -> matched candidate row

    for c_id, config in legacy_overrides.items():
        candidates = inf_eventful_by_cid.get(c_id, [])
        found = None
        for candidate in candidates:
            if _matches(candidate, config):
                found = candidate
                break
        if found is None:
            print(
                f"  [WARN] corpus_id={c_id}: no INF_EVENTFUL candidate matched "
                f"the legacy config {config}"
            )
            unmatched.append(c_id)
        else:
            matched[c_id] = found
            print(
                f"  [OK]   corpus_id={c_id}: matched → h_grade={found.get('h_grade')}"
            )

    if unmatched:
        print(
            f"\n[ERROR] {len(unmatched)} legacy shim(s) could not be matched in "
            "validated_reconstructable_roots.csv. Aborting — nothing written."
        )
        print(
            "Tip: re-run the reconstruct_and_validate phase so that the INF_EVENTFUL "
            "candidates are present, then re-run this script."
        )
        sys.exit(1)

    # ── 4. Build new-format rows for all stative corpus_ids ───────────────────
    # We only write rows for corpus_ids that had a legacy curated entry.
    # (The full candidate set will be regenerated by the pipeline on next run.)
    output_rows: list[dict] = []
    for c_id in sorted(
        legacy_overrides.keys(), key=lambda x: int(x) if x.isdigit() else 0
    ):
        candidates = inf_eventful_by_cid.get(c_id, [])
        chosen = matched.get(c_id)
        for candidate in candidates:
            new_row = dict(candidate)
            new_row["user_selected"] = (
                "x" if (chosen is not None and candidate is chosen) else ""
            )
            # Keep pipeline_selected as-is from the validated roots CSV
            output_rows.append(new_row)

    # ── 5. Write new stative_shims.csv ────────────────────────────────────────
    with open(STATIVE_SHIMS_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=new_fieldnames,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(output_rows)

    print(
        f"\n[DONE] Wrote {len(output_rows)} row(s) to curated/stative_shims.csv "
        f"(new multi-row format)."
    )


if __name__ == "__main__":
    main()
