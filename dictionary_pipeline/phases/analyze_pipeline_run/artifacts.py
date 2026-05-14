import csv
import json
import os
from typing import Any

from dictionary_pipeline.paths import (
    CLASS_MATCH_COUNTS_PATH,
    FURTHEST_CORPUS_BY_ID_PATH,
    MACRO_VARIANT_DATA_PATH,
    ROOT_AMBIGUITY_COUNTS_PATH,
    ROOT_MACRO_DISTRIBUTION_PATH,
    UNMATCHED_VERBS_PATH,
    UNUSED_VARIANTS_PATH,
    VARIANT_MATCH_COUNTS_PATH,
    VARIATION_MATCH_COUNTS_PATH,
    VERB_COVERAGE_PATH,
)

# --- Private generic I/O helpers ---


def _load_csv(path: str) -> list[dict[str, str]]:
    if not os.path.exists(path):
        return []
    with open(path, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _save_csv(path: str, data: list[dict[str, Any]], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def _save_json(path: str, data: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode="w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def _load_json(path: str) -> Any:
    if not os.path.exists(path):
        return None
    with open(path, mode="r", encoding="utf-8") as f:
        return json.load(f)


# --- Output Artifacts (Written by this phase) ---


def save_class_match_counts(data, fieldnames):
    _save_csv(CLASS_MATCH_COUNTS_PATH, data, fieldnames)


def load_class_match_counts():
    return _load_csv(CLASS_MATCH_COUNTS_PATH)


def save_verb_coverage(data):
    _save_json(VERB_COVERAGE_PATH, data)


def load_verb_coverage():
    return _load_json(VERB_COVERAGE_PATH)


def save_unmatched_verbs(data, fieldnames):
    _save_csv(UNMATCHED_VERBS_PATH, data, fieldnames)


def load_unmatched_verbs():
    return _load_csv(UNMATCHED_VERBS_PATH)


def save_root_ambiguity_counts(data, fieldnames):
    _save_csv(ROOT_AMBIGUITY_COUNTS_PATH, data, fieldnames)


def load_root_ambiguity_counts():
    return _load_csv(ROOT_AMBIGUITY_COUNTS_PATH)


def save_macro_variant_data(data):
    _save_json(MACRO_VARIANT_DATA_PATH, data)


def load_macro_variant_data():
    return _load_json(MACRO_VARIANT_DATA_PATH)


def save_variant_match_counts(data, fieldnames):
    _save_csv(VARIANT_MATCH_COUNTS_PATH, data, fieldnames)


def load_variant_match_counts():
    return _load_csv(VARIANT_MATCH_COUNTS_PATH)


def save_variation_match_counts(data, fieldnames):
    _save_csv(VARIATION_MATCH_COUNTS_PATH, data, fieldnames)


def load_variation_match_counts():
    return _load_csv(VARIATION_MATCH_COUNTS_PATH)


def save_unused_variants(data):
    _save_json(UNUSED_VARIANTS_PATH, data)


def load_unused_variants():
    return _load_json(UNUSED_VARIANTS_PATH)


def save_root_macro_distribution(data, fieldnames):
    _save_csv(ROOT_MACRO_DISTRIBUTION_PATH, data, fieldnames)


def load_root_macro_distribution():
    return _load_csv(ROOT_MACRO_DISTRIBUTION_PATH)


def save_furthest_corpus_by_id(data, fieldnames):
    _save_csv(FURTHEST_CORPUS_BY_ID_PATH, data, fieldnames)


def load_furthest_corpus_by_id():
    return _load_csv(FURTHEST_CORPUS_BY_ID_PATH)
