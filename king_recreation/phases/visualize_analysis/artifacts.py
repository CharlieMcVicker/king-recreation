import os

from king_recreation.paths import (
    CLASS_ENDING_PROFILES_CSV_PATH,
    CLASS_MATCH_COUNTS_PATH,
    CLASS_NEAR_MISSES_PATH,
    MACRO_VARIANT_DATA_PATH,
    ROOT_AMBIGUITY_COUNTS_PATH,
    VARIANT_MATCH_COUNTS_PATH,
    VARIATION_MATCH_COUNTS_PATH,
    VERB_COVERAGE_PATH,
    VISUALIZATIONS_PATH,
)


def get_class_match_counts_path() -> str:
    return CLASS_MATCH_COUNTS_PATH


def get_verb_coverage_path() -> str:
    return VERB_COVERAGE_PATH


def get_class_near_misses_path() -> str:
    return CLASS_NEAR_MISSES_PATH


def get_root_ambiguity_counts_path() -> str:
    return ROOT_AMBIGUITY_COUNTS_PATH


def get_macro_variant_data_path() -> str:
    return MACRO_VARIANT_DATA_PATH


def get_variant_match_counts_path() -> str:
    return VARIANT_MATCH_COUNTS_PATH


def get_variation_match_counts_path() -> str:
    return VARIATION_MATCH_COUNTS_PATH


def get_class_ending_profiles_path() -> str:
    return CLASS_ENDING_PROFILES_CSV_PATH


def get_visualizations_dir() -> str:
    os.makedirs(VISUALIZATIONS_PATH, exist_ok=True)
    return VISUALIZATIONS_PATH
