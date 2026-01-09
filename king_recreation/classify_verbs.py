import csv
import os

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
    literal_suffix = pattern_suffix.replace("*", "").replace("@", "")
    
    # 2. Strip literal ending (if possible)
    if not corpus_form.endswith(literal_suffix):
        # Even if it's loose match, we use literal stripping for full match?
        # Actually, if strictness is loose, we should check if normalized form matches
        if not strict and normalize(corpus_form).endswith(normalize(literal_suffix)):
            # This is tricky. How to strip normalized suffix from non-normalized form?
            # Let's find the split point by length of normalized suffix from the end of normalized form.
            norm_form = normalize(corpus_form)
            norm_suffix = normalize(literal_suffix)
            # Find how many 'h' were removed in the suffix part? No.
            # Easiest: reveal Candidate Stem in normalized space.
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
            # Re-get candidate stem raw if strict
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
                # match_ending now handles empty form_val correctly
                if not match_ending(form_val, cls[form], is_strict_bool):
                    all_endings_match = False
                    break
            
            # Calculate Stem Final matches for ALL forms regardless of ending match
            sf_matches = {}
            for form in forms:
                form_val = verb.get(form)
                sf_matches[f"stem_final_match_{form}"] = calculate_stem_final_match(
                    form_val, cls[form], stem_final, is_strict_bool
                )
            
            # All 5 forms satisfy both Ending Match and Stem Final check for Full Match
            all_sf_match = all(sf_matches.values())
            
            # If Ending Match passes, record the highest scope match
            if all_endings_match:
                scope = "full" if all_sf_match else "ending"
                matches.append({
                    "definition": definition,
                    "class": class_id,
                    "strictness": strictness,
                    "scope": scope,
                    **sf_matches
                })
    return matches

def classify_verbs():
    classes_path = "data/king_classes.csv"
    corpus_path = "artifacts/data/corpus.csv"
    output_path = "artifacts/data/matches.csv"

    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        return

    # Load classes
    classes = []
    with open(classes_path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            classes.append(row)

    # Load corpus
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
    classify_verbs()
