import argparse

from king_recreation.analyze_connections import analyze_connections
from king_recreation.analyze_matches import analyze_matches
from king_recreation.classify_verbs import classify_verbs
from king_recreation.dedupe_roots import main as dedupe_roots
from king_recreation.derive_stems import main as derive_stems
from king_recreation.group_hierarchical import main as group_hierarchical
from king_recreation.paths import (
    cherokee_nation_dictionary_path,
    corpus_path,
    derivational_connections_path,
    reconstructable_verbs_path,
)
from king_recreation.preprocess_ced import process_cn_dict
from king_recreation.reconstruction import main as reconstruct_from_roots
from king_recreation.tone.check_tone_consistency import main as check_tone_consistency
from king_recreation.utils import group_verbs_by_root, load_verbs
from king_recreation.visualize_analysis import run_all_visualizations


def main():
    parser = argparse.ArgumentParser(description="King Recreation Pipeline")
    parser.add_argument("--classes", help="Path to custom classes CSV file")
    args = parser.parse_args()
    print("[1/10] Preprocessing Cherokee Nation Dictionary...")
    process_cn_dict(cherokee_nation_dictionary_path, corpus_path)

    print("\n[2/10] Classifying Verbs...")
    classify_verbs(args.classes)

    print("\n[3/10] Deduping Roots...")
    dedupe_roots()

    print("\n[4/10] Deriving Stems...")
    derive_stems()

    print("\n[5/10] Reconstructing From Roots...")
    reconstruct_from_roots()

    print("\n[6/10] Analyzing Derivational Suffix Connections...")
    analyze_connections(
        reconstructable_verbs_path,
        derivational_connections_path,
        args.classes,
    )

    print("\n[7/10] Grouping Dictionary Hierarchically...")
    group_hierarchical()

    print("\n[8/10] Checking Tone Consistency and Generating Profiles...")
    check_tone_consistency(interactive=False)

    print("\n[9/10] Analyzing Matches...")
    analyze_matches(args.classes)

    print("\n[10/10] Visualizing Analysis...")
    run_all_visualizations()


if __name__ == "__main__":
    main()
