import argparse
from king_recreation.preprocess_ced import process_ced
from king_recreation.derive_stems import main as derive_stems
from king_recreation.classify_verbs import classify_verbs
from king_recreation.analyze_matches import analyze_matches
from king_recreation.visualize_analysis import run_all_visualizations
from king_recreation.reconstruct_from_roots import main as reconstruct_from_roots


def main():
    parser = argparse.ArgumentParser(description="King Recreation Pipeline")
    parser.add_argument("--classes", help="Path to custom classes CSV file")
    args = parser.parse_args()

    print("Starting King Recreation Pipeline...")

    print("\n[1/6] Preprocessing CED Data...")
    process_ced()

    print("\n[2/6] Deriving Stems and Pronominal Patterns...")
    derive_stems()

    print("\n[3/6] Classifying Verbs...")
    classify_verbs(args.classes)

    print("\n[4/6] Analyzing Matches...")
    analyze_matches(args.classes)

    print("\n[5/6] Reconstructing from Roots...")
    reconstruct_from_roots(args.classes)

    print("\n[6/6] Visualizing Analysis...")
    run_all_visualizations()

    print("\nPipeline Complete!")


if __name__ == "__main__":
    main()
