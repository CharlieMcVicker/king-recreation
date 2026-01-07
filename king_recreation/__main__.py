import sys
from king_recreation.preprocess_ced import process_ced
from king_recreation.classify_verbs import classify_verbs
from king_recreation.analyze_matches import analyze_matches
from king_recreation.visualize_analysis import run_all_visualizations

def main():
    print("Starting King Recreation Pipeline...")

    print("\n[1/4] Preprocessing CED Data...")
    process_ced()

    print("\n[2/4] Classifying Verbs...")
    classify_verbs()

    print("\n[3/4] Analyzing Matches...")
    analyze_matches()

    print("\n[4/4] Visualizing Analysis...")
    run_all_visualizations()

    print("\nPipeline Complete!")

if __name__ == "__main__":
    main()
