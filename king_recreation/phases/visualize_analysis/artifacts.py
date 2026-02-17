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


def get_class_match_counts_path():
    return CLASS_MATCH_COUNTS_PATH


def get_verb_coverage_path():
    return VERB_COVERAGE_PATH


def get_class_near_misses_path():
    return CLASS_NEAR_MISSES_PATH


def get_root_ambiguity_counts_path():
    return ROOT_AMBIGUITY_COUNTS_PATH


def get_macro_variant_data_path():
    return MACRO_VARIANT_DATA_PATH


def get_variant_match_counts_path():
    return VARIANT_MATCH_COUNTS_PATH


def get_variation_match_counts_path():
    return VARIATION_MATCH_COUNTS_PATH


def get_class_ending_profiles_path():
    return CLASS_ENDING_PROFILES_CSV_PATH


def get_visualizations_dir():
    os.makedirs(VISUALIZATIONS_PATH, exist_ok=True)
    return VISUALIZATIONS_PATH
