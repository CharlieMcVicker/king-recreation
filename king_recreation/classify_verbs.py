import csv
import os
from king_recreation.stem_analysis import check_root_consistency

def normalize(s):
    if s is None:
        return ""
    return s.replace("h", "")

def match_ending(corpus_form, pattern_suffix, strict):
    # Policy: Vacuous Matching
    # If the corpus form is missing, it cannot contradict any pattern.
    if not corpus_form:
        return True

    # Literal characters only, ignore * or @
    if pattern_suffix is None:
        pattern_suffix = ""
    literal_suffix = pattern_suffix.replace("*", "").replace("@", "")
    
    if strict:
        return corpus_form.endswith(literal_suffix)
    else:
        return normalize(corpus_form).endswith(normalize(literal_suffix))

def calculate_stem_final_match(corpus_form, pattern_suffix, stem_final_str, strict):
    # Policy: Vacuous Matching
    if not corpus_form:
        return True

    # 1. Identify literal ending
    if pattern_suffix is None:
        pattern_suffix = ""
    literal_suffix = pattern_suffix.replace("*", "").replace("@", "")
    
    # 2. Strip literal ending (if possible)
    if not corpus_form.endswith(literal_suffix):
        if not strict and normalize(corpus_form).endswith(normalize(literal_suffix)):
            norm_form = normalize(corpus_form)
            norm_suffix = normalize(literal_suffix)
            candidate_stem_norm = norm_form[:-len(norm_suffix)] if len(norm_suffix) > 0 else norm_form
        else:
            return False
    else:
        candidate_stem_raw = corpus_form[:-len(literal_suffix)] if len(literal_suffix) > 0 else corpus_form
        candidate_stem_norm = normalize(candidate_stem_raw)

    # 3. Adjust stem final based on modifiers
    stem_finals = stem_final_str.split(";") if stem_final_str else [""]
    
    match = False
    for sf in stem_finals:
        sf_adjusted = sf
        if "*" in pattern_suffix:
            if len(sf_adjusted) >= 1:
                sf_adjusted = sf_adjusted[:-1]
        elif "@" in pattern_suffix:
            if len(sf_adjusted) >= 2:
                sf_adjusted = sf_adjusted[:-2]
        
        # 4. Verify candidate stem
        sf_norm = normalize(sf_adjusted)
        if strict:
            candidate_stem_strict = corpus_form[:-len(literal_suffix)] if len(literal_suffix) > 0 else corpus_form
            if candidate_stem_strict.endswith(sf_adjusted):
                match = True
                break
        else:
            if candidate_stem_norm.endswith(sf_norm):
                match = True
                break
    return match

def get_matches_for_verb(verb, classes):
    forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]
    matches = []
    
    definition = verb.get("definition", "unknown")
    
    for cls in classes:
        class_id = cls["class"]
        stem_final = cls["stem final"]
        
        for strictness in ["strict", "loose"]:
            is_strict_bool = (strictness == "strict")
            
            # Check Ending Match
            all_endings_match = True
            for form in forms:
                form_val = verb.get(form)
                if not match_ending(form_val, cls[form], is_strict_bool):
                    all_endings_match = False
                    break
            
            # Calculate Stem Final matches
            sf_matches = {}
            for form in forms:
                form_val = verb.get(form)
                sf_matches[f"stem_final_match_{form}"] = calculate_stem_final_match(
                    form_val, cls[form], stem_final, is_strict_bool
                )
            
            all_sf_match = all(sf_matches.values())
            
            if all_endings_match:
                scope = "ending"
                if all_sf_match:
                    scope = "full"
                    
                    # New: Check for Root Consistency -> 'reconstructs'
                    if is_strict_bool:
                        consistent, root, details = check_root_consistency(verb, cls)
                        if consistent:
                            scope = "reconstructs"

                matches.append({
                    "definition": definition,
                    "class": class_id,
                    "strictness": strictness,
                    "scope": scope,
                    **sf_matches
                })
    return matches

def classify_verbs(classes_path=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if classes_path is None:
        classes_path = os.path.join(base_dir, "data", "king_classes.csv")
    corpus_path = os.path.join(base_dir, "artifacts", "data", "stem_corpus.csv")
    output_path = os.path.join(base_dir, "artifacts", "data", "matches.csv")

    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found. Ensure stem derivation is run first.")
        return

    # Load classes
    classes = []
    with open(classes_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            classes.append(row)

    # Load stem corpus
    verbs = []
    with open(corpus_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            verbs.append(row)

    matches_data = []

    for verb in verbs:
        matches_data.extend(get_matches_for_verb(verb, classes))

    fieldnames = [
        "definition", "class", "strictness", "scope",
        "stem_final_match_present", "stem_final_match_imperfective",
        "stem_final_match_perfective", "stem_final_match_imperative",
        "stem_final_match_infinitive"
    ]
    
    with open(output_path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches_data)

    print(f"Matches written to {output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Classify verbs using King's classes.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    classify_verbs(args.classes)
