import os

# -----------------------------------------------------------------------------
# Base Directories
# -----------------------------------------------------------------------------
DATA_DIR = "data"
ARTIFACTS_DIR = "artifacts"

ARTIFACTS_DATA_DIR = os.path.join(ARTIFACTS_DIR, "data")
CONNECTIONS_DIR = os.path.join(ARTIFACTS_DIR, "connections")
REPORTS_DIR = os.path.join(ARTIFACTS_DIR, "reports")
VISUALIZATIONS_DIR = os.path.join(ARTIFACTS_DIR, "visualizations")


# -----------------------------------------------------------------------------
# 1. Pipeline Inputs (Immutable Data)
# -----------------------------------------------------------------------------
cherokee_nation_dictionary_path = os.path.join(
    DATA_DIR, "cherokee_nation_dictionary.csv"
)
ced_data_original_path = os.path.join(DATA_DIR, "ced_data_original.csv")
post_root_morphemes_path = os.path.join(DATA_DIR, "post_root_morphemes.csv")
classes_data_path = os.path.join(DATA_DIR, "classes.csv")


# -----------------------------------------------------------------------------
# 2. Intermediate Corpora & Analysis Data
# -----------------------------------------------------------------------------
corpus_path = os.path.join(ARTIFACTS_DATA_DIR, "corpus.csv")
stripped_path = os.path.join(ARTIFACTS_DATA_DIR, "endings_stripped_corpus.csv")
derived_roots_path = os.path.join(ARTIFACTS_DATA_DIR, "derived_roots.csv")

# Match Data
matches_path = os.path.join(ARTIFACTS_DATA_DIR, "matches_initial.csv")
validated_matches_path = os.path.join(ARTIFACTS_DATA_DIR, "matches_validated.csv")

# Connections (Manual & Automated)
root_connections_path = os.path.join(CONNECTIONS_DIR, "root_connections.csv")
post_root_connections_path = os.path.join(CONNECTIONS_DIR, "post_root_connections.csv")


# -----------------------------------------------------------------------------
# 3. Final Outputs (JSON/CSV for App or Consumption)
# -----------------------------------------------------------------------------
# Main Application Data
reconstructable_verbs_path = os.path.join(
    ARTIFACTS_DATA_DIR, "reconstructable_verbs.json"
)
hierarchical_dict_path = os.path.join(ARTIFACTS_DATA_DIR, "hierarchical-dict.json")
classes_expanded_path = os.path.join(ARTIFACTS_DATA_DIR, "classes_expanded.json")

# Supplementary Data
root_ids_path = os.path.join(ARTIFACTS_DATA_DIR, "root_ids.csv")
roots_by_class_path = os.path.join(ARTIFACTS_DATA_DIR, "roots_by_class.csv")
root_macro_distribution_path = os.path.join(
    ARTIFACTS_DATA_DIR, "root_macro_distribution.csv"
)


# -----------------------------------------------------------------------------
# 4. Reports & Logs
# -----------------------------------------------------------------------------
reports_path = REPORTS_DIR  # Legacy alias
pre_parsing_failures_path = os.path.join(REPORTS_DIR, "stem_derivation_failures.csv")
open_forms_report_path = os.path.join(REPORTS_DIR, "open_forms.json")
consistency_analysis_path = os.path.join(REPORTS_DIR, "consistency_analysis.csv")
reconstruction_report_path = os.path.join(REPORTS_DIR, "reconstruction_report.csv")
reconstruction_validation_path = os.path.join(
    REPORTS_DIR, "reconstruction_validation.json"
)
reconstruction_failures_path = os.path.join(REPORTS_DIR, "reconstruction_failures.csv")

# Statistics
class_match_counts_path = os.path.join(REPORTS_DIR, "class_match_counts.csv")
verb_coverage_path = os.path.join(REPORTS_DIR, "verb_coverage.json")
unmatched_verbs_path = os.path.join(REPORTS_DIR, "unmatched_verbs.csv")
root_ambiguity_counts_path = os.path.join(REPORTS_DIR, "root_ambiguity_counts.csv")
macro_variant_data_path = os.path.join(REPORTS_DIR, "macro_variant_data.json")
variant_match_counts_path = os.path.join(REPORTS_DIR, "variant_match_counts.csv")
variation_match_counts_path = os.path.join(REPORTS_DIR, "variation_match_counts.csv")
unused_variants_path = os.path.join(REPORTS_DIR, "unused_variants.json")
class_near_misses_path = os.path.join(REPORTS_DIR, "class_near_misses.csv")


# -----------------------------------------------------------------------------
# 5. Visualizations
# -----------------------------------------------------------------------------
visualizations_path = VISUALIZATIONS_DIR
