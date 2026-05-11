import csv
import io
import json
import os
from typing import Any

from king_recreation.paths import (
    CHEROKEE_NATION_DICTIONARY_PATH,
    CLASS_ENDING_PROFILES_CSV_PATH,
    ENDING_TONE_ANALYSIS_CSV_PATH,
    ENDING_TONE_ANALYSIS_JSON_PATH,
)


def load_cnd_corpus() -> dict[str, dict[str, str]]:
    if not os.path.exists(CHEROKEE_NATION_DICTIONARY_PATH):
        return {}
    with open(CHEROKEE_NATION_DICTIONARY_PATH, "r", encoding="utf-8") as f:
        content = f.read()
        if content.startswith("\ufeff"):
            content = content[1:]
        reader = csv.DictReader(io.StringIO(content))
        return {r.get("Entry No.", "").strip(): r for r in reader}


def save_tone_analysis_json(data: Any):
    os.makedirs(os.path.dirname(ENDING_TONE_ANALYSIS_JSON_PATH), exist_ok=True)
    with open(ENDING_TONE_ANALYSIS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, sort_keys=True)


def load_tone_analysis_json() -> Any:
    if not os.path.exists(ENDING_TONE_ANALYSIS_JSON_PATH):
        return None
    with open(ENDING_TONE_ANALYSIS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_tone_analysis_csv(data: list[dict[str, Any]], fieldnames: list[str]) -> None:
    os.makedirs(os.path.dirname(ENDING_TONE_ANALYSIS_CSV_PATH), exist_ok=True)
    with open(ENDING_TONE_ANALYSIS_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_tone_analysis_csv() -> list[dict[str, Any]]:
    if not os.path.exists(ENDING_TONE_ANALYSIS_CSV_PATH):
        return []
    with open(ENDING_TONE_ANALYSIS_CSV_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_class_ending_profiles(
    data: list[dict[str, Any]], fieldnames: list[str]
) -> None:
    os.makedirs(os.path.dirname(CLASS_ENDING_PROFILES_CSV_PATH), exist_ok=True)
    with open(CLASS_ENDING_PROFILES_CSV_PATH, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def load_class_ending_profiles() -> list[dict[str, Any]]:
    if not os.path.exists(CLASS_ENDING_PROFILES_CSV_PATH):
        return []
    with open(CLASS_ENDING_PROFILES_CSV_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))
