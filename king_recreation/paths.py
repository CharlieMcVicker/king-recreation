import os

# -----------------------------------------------------------------------------
# Base Directories
# -----------------------------------------------------------------------------
DATA_DIR = "data"
ARTIFACTS_DIR = "artifacts"

ARTIFACTS_DATA_DIR = os.path.join(ARTIFACTS_DIR, "data")
ARTIFACTS_CORPORA_DIR = os.path.join(ARTIFACTS_DIR, "corpora")
CONNECTIONS_DIR = os.path.join(ARTIFACTS_DIR, "connections")
REPORTS_DIR = os.path.join(ARTIFACTS_DIR, "reports")
VISUALIZATIONS_DIR = os.path.join(ARTIFACTS_DIR, "visualizations")


# -----------------------------------------------------------------------------
# 1. Pipeline Inputs (Immutable Data)
# -----------------------------------------------------------------------------
CHEROKEE_NATION_DICTIONARY_PATH = os.path.join(
    DATA_DIR, "cherokee_nation_dictionary.csv"
)
CED_DATA_ORIGINAL_PATH = os.path.join(DATA_DIR, "ced_data_original.csv")
POST_ROOT_MORPHEMES_PATH = os.path.join(DATA_DIR, "post_root_morphemes.csv")
CLASSES_DATA_PATH = os.path.join(DATA_DIR, "classes.csv")


# -----------------------------------------------------------------------------
# 2. Intermediate Corpora & Analysis Data
# -----------------------------------------------------------------------------
CORPUS_PATH = os.path.join(ARTIFACTS_CORPORA_DIR, "corpus.csv")
CORPUS_NO_ASP_PATH = os.path.join(ARTIFACTS_CORPORA_DIR, "corpus_no_asp.csv")
CORPUS_NO_PRE_NO_ASP_PATH = os.path.join(
    ARTIFACTS_CORPORA_DIR, "corpus_no_pre_no_asp.csv"
)
VALIDATED_RECONSTRUCTABLE_ROOTS_PATH = os.path.join(
    ARTIFACTS_CORPORA_DIR, "validated_reconstructable_roots.csv"
)
CORPUS_TO_CND_PATH = os.path.join(ARTIFACTS_CORPORA_DIR, "corpus_to_cnd.csv")
STEMS_WITH_TONE_CORPUS_PATH = os.path.join(
    ARTIFACTS_CORPORA_DIR, "stems_with_tone_corpus.csv"
)
UNDERLYING_STEMS_PATH = os.path.join(ARTIFACTS_DATA_DIR, "underlying_stems.csv")

# Match Data
MATCHES_PATH = os.path.join(ARTIFACTS_DATA_DIR, "matches_initial.csv")
VALIDATED_MATCHES_PATH = os.path.join(ARTIFACTS_DATA_DIR, "matches_validated.csv")

# Connections (Manual & Automated)
DERIVATIONAL_CONNECTIONS_PATH = os.path.join(
    CONNECTIONS_DIR, "derivational_suffix_connections.csv"
)


# -----------------------------------------------------------------------------
# 3. Final Outputs (JSON/CSV for App or Consumption)
# -----------------------------------------------------------------------------
# Main Application Data
RECONSTRUCTABLE_VERBS_PATH = os.path.join(
    ARTIFACTS_DATA_DIR, "reconstructable_verbs.json"
)
HIERARCHICAL_DICT_PATH = os.path.join(ARTIFACTS_DATA_DIR, "hierarchical-dict.json")
CLASSES_EXPANDED_PATH = os.path.join(ARTIFACTS_DATA_DIR, "classes_expanded.json")

# Supplementary Data
ROOT_IDS_PATH = os.path.join(ARTIFACTS_DATA_DIR, "root_ids.csv")
ROOTS_BY_CLASS_PATH = os.path.join(ARTIFACTS_DATA_DIR, "roots_by_class.csv")
ROOT_MACRO_DISTRIBUTION_PATH = os.path.join(
    ARTIFACTS_DATA_DIR, "root_macro_distribution.csv"
)


# -----------------------------------------------------------------------------
# 4. Reports & Logs
# -----------------------------------------------------------------------------
REPORTS_PATH = REPORTS_DIR  # Legacy alias
PRE_PARSING_FAILURES_PATH = os.path.join(REPORTS_DIR, "stem_derivation_failures.csv")
OPEN_FORMS_REPORT_PATH = os.path.join(REPORTS_DIR, "open_forms.json")
CONSISTENCY_ANALYSIS_PATH = os.path.join(REPORTS_DIR, "consistency_analysis.csv")
RECONSTRUCTION_REPORT_PATH = os.path.join(REPORTS_DIR, "reconstruction_report.csv")
RECONSTRUCTION_VALIDATION_PATH = os.path.join(
    REPORTS_DIR, "reconstruction_validation.json"
)
RECONSTRUCTION_FAILURES_PATH = os.path.join(REPORTS_DIR, "reconstruction_failures.csv")
FURTHEST_CORPUS_BY_ID_PATH = os.path.join(REPORTS_DIR, "furthest_corpus_by_id.csv")
ENDING_TONE_ANALYSIS_JSON_PATH = os.path.join(REPORTS_DIR, "ending_tone_analysis.json")
ENDING_TONE_ANALYSIS_CSV_PATH = os.path.join(REPORTS_DIR, "ending_tone_analysis.csv")
CLASS_ENDING_PROFILES_CSV_PATH = os.path.join(REPORTS_DIR, "class_ending_profiles.csv")

# Statistics
CLASS_MATCH_COUNTS_PATH = os.path.join(REPORTS_DIR, "class_match_counts.csv")
VERB_COVERAGE_PATH = os.path.join(REPORTS_DIR, "verb_coverage.json")
UNMATCHED_VERBS_PATH = os.path.join(REPORTS_DIR, "unmatched_verbs.csv")
ROOT_AMBIGUITY_COUNTS_PATH = os.path.join(REPORTS_DIR, "root_ambiguity_counts.csv")
MACRO_VARIANT_DATA_PATH = os.path.join(REPORTS_DIR, "macro_variant_data.json")
VARIANT_MATCH_COUNTS_PATH = os.path.join(REPORTS_DIR, "variant_match_counts.csv")
VARIATION_MATCH_COUNTS_PATH = os.path.join(REPORTS_DIR, "variation_match_counts.csv")
UNUSED_VARIANTS_PATH = os.path.join(REPORTS_DIR, "unused_variants.json")
CLASS_NEAR_MISSES_PATH = os.path.join(REPORTS_DIR, "class_near_misses.csv")


# -----------------------------------------------------------------------------
# 5. Visualizations
# -----------------------------------------------------------------------------
VISUALIZATIONS_PATH = VISUALIZATIONS_DIR


# -----------------------------------------------------------------------------
# 6. TeX Dictionary Outputs
# -----------------------------------------------------------------------------
TEX_DIR = os.path.join(ARTIFACTS_DIR, "tex")
TEX_ROOTS_DIR = os.path.join(TEX_DIR, "roots")
MAIN_TEX_PATH = os.path.join(TEX_DIR, "main.tex")
