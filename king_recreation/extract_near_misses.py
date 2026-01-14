import csv
import argparse
import os


def load_csv(path):
    with open(path, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_csv(path, data, fieldnames):
    with open(path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)


def extract_near_misses(class_id, strictness):
    matches_path = "artifacts/data/matches.csv"
    corpus_path = "artifacts/data/corpus.csv"
    output_dir = "artifacts/debug"
    os.makedirs(output_dir, exist_ok=True)

    output_path = os.path.join(output_dir, f"near_misses_{class_id}_{strictness}.csv")

    if not os.path.exists(matches_path):
        print(f"Error: {matches_path} not found.")
        return
    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        return

    matches = load_csv(matches_path)
    corpus = load_csv(corpus_path)

    # Create a lookup for corpus data by definition
    corpus_lookup = {row["definition"]: row for row in corpus}

    # Filter matches for near misses (ending match yes, full match no)
    # The requirement is "identify a verb class with many matches and one form that is failing for full match"
    # In my analysis, Ic loose matches have 15 verbs, and all are near misses (scope='ending') because perfective failing.

    near_miss_results = []
    for m in matches:
        if m["class"] == class_id and m["strictness"] == strictness:
            if m["scope"] == "ending":
                definition = m["definition"]
                corpus_row = corpus_lookup.get(definition, {})

                # Combine match info with corpus info
                combined = {**m, **corpus_row}
                near_miss_results.append(combined)

    if not near_miss_results:
        print(
            f"No near misses found for class {class_id} with strictness {strictness}."
        )
        return

    # Define fieldnames: match columns first, then corpus columns
    match_cols = [
        "definition",
        "class",
        "strictness",
        "scope",
        "stem_final_match_present",
        "stem_final_match_imperfective",
        "stem_final_match_perfective",
        "stem_final_match_imperative",
        "stem_final_match_infinitive",
    ]
    corpus_cols = ["present", "imperfective", "perfective", "imperative", "infinitive"]

    # Filter out definition if it's already in match_cols
    all_fieldnames = match_cols + corpus_cols

    save_csv(output_path, near_miss_results, all_fieldnames)
    print(f"Near miss data saved to {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract near miss data for a specific class."
    )
    parser.add_argument("--class_id", required=True, help="Verb class ID (e.g., Ic)")
    parser.add_argument(
        "--strictness",
        choices=["strict", "loose"],
        default="loose",
        help="Match strictness",
    )
    args = parser.parse_args()

    extract_near_misses(args.class_id, args.strictness)
