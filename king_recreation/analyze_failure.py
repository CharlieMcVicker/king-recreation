import csv
import sys
import json
import argparse
import os

# Ensure the project root is in sys.path
sys.path.append(os.getcwd())

from king_recreation.derive_stems import StemDeriver
from king_recreation.phonology_data import get_pronominal_set_name, PRONOMINAL_PREFIXES_MAP, Condition

def analyze_failure(target_definition):
    deriver = StemDeriver()
    row = None
    
    # Find the row in corpus.csv
    # Assuming the script is run from the project root
    corpus_path = os.path.join('artifacts', 'data', 'corpus.csv')
    if not os.path.exists(corpus_path):
        # Fallback for when running from within king_recreation or other contexts
        corpus_path = os.path.join('..', 'artifacts', 'data', 'corpus.csv')

    with open(corpus_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r['definition'] == target_definition:
                row = r
                break
    
    if not row:
        print(json.dumps({"error": f"Could not find definition '{target_definition}' in corpus."}))
        return

    form_names = ['present', 'present_1sg', 'imperfective', 'perfective', 'imperative', 'infinitive']
    forms = {fn: row[fn] for fn in form_names if row.get(fn)}
    
    analysis = {
        "definition": target_definition,
        "forms": forms,
        "configurations": []
    }

    # Limit the number of returned configs to avoid massive JSON response
    # We will prioritize:
    # 1. Configs that are fully successful (if any - unlikely for failures)
    # 2. Configs that are consistent but maybe failed some other check?
    # 3. Configs where ALL forms produced at least one stem (Inconsistent)
    # 4. A sample of configs where some forms failed.

    configs_data = []

    for set_type in ['Set A', 'Set B']:
        for imp_type in ['normal', 'to_3rd']:
            for t in [True, False]:
                for p in [True, False]:
                    for d in [True, False]:
                        config_desc = {
                            "set_type": set_type,
                            "imp_type": imp_type,
                            "translocutive": t,
                            "partitive": p,
                            "distributive": d,
                        }
                        
                        possible_stems = {fn: [] for fn in forms}
                        failed_forms = []

                        for fn, word in forms.items():
                            current_words = [('', word)]
                            
                            # Match Prepronominals
                            for exists, p_type in [(t, 'T'), (p, 'P'), (d, 'D')]:
                                next_words = []
                                for _, w in current_words:
                                    next_words.extend(deriver.match_prepronominal(w, exists, p_type, fn))
                                current_words = list(set(next_words))
                            
                            # Match Pronominal Prefix
                            pron_type = get_pronominal_set_name(fn, set_type, imp_type)
                            prefixes = PRONOMINAL_PREFIXES_MAP[pron_type]
                            
                            found_stem_for_form = False
                            for _, w in current_words:
                                for pref, cond in prefixes:
                                    if pref == 'ø':
                                        if w and cond == Condition.VOWEL_AE and w[0] in 'ae':
                                            possible_stems[fn].append(w)
                                            found_stem_for_form = True
                                    elif w.startswith(pref.replace('-', '')):
                                        remainder = w[len(pref.replace('-', '')):]
                                        if cond == Condition.A_REPLACE:
                                            possible_stems[fn].append('a' + remainder)
                                            found_stem_for_form = True
                                        elif cond == Condition.V and pref == 'uwa-':
                                            possible_stems[fn].append('v' + remainder)
                                            found_stem_for_form = True
                                        else:
                                            possible_stems[fn].append(remainder)
                                            found_stem_for_form = True
                            
                            if not found_stem_for_form:
                                failed_forms.append(fn)

                        # Determine outcome
                        outcome = ""
                        consistent_stems = []
                        
                        if failed_forms:
                            outcome = "Form Failure"
                        else:
                            # Check consistency across all forms
                            # We need to find at least one stem start char that is present in ALL forms' possible stems
                            # This is a simplified consistency check.
                            
                            # Flatten all stems to find common initials
                            all_initials = set()
                            for fn in possible_stems:
                                for s in possible_stems[fn]:
                                    if s: all_initials.add(s[0])
                            
                            valid_initials = []
                            for initial in all_initials:
                                is_consistent = True
                                for fn in possible_stems:
                                    if not any(s and s.startswith(initial) for s in possible_stems[fn]):
                                        is_consistent = False
                                        break
                                if is_consistent:
                                    valid_initials.append(initial)
                            
                            if valid_initials:
                                outcome = "Success" # Or at least "Consistent"
                                # Collect the stems that match the valid initials
                                consistent_stems = {fn: [s for s in possible_stems[fn] if s and s[0] in valid_initials] for fn in possible_stems}
                            else:
                                outcome = "Inconsistent"

                        config_result = {
                            "config": config_desc,
                            "outcome": outcome,
                            "failed_forms": failed_forms,
                            "possible_stems": possible_stems,
                            "consistent_stems": consistent_stems
                        }
                        configs_data.append(config_result)

    # Sort configs to put "Success" first, then "Inconsistent", then "Form Failure"
    def score_config(c):
        if c["outcome"] == "Success": return 3
        if c["outcome"] == "Inconsistent": return 2
        if c["outcome"] == "Form Failure": return 1
        return 0
    
    configs_data.sort(key=score_config, reverse=True)
    
    # Return top 20 most relevant configs to avoid huge payload
    # Or return all if not too many? There are 2*2*2*2*2 = 32 configs. That's small enough.
    analysis["configurations"] = configs_data

    print(json.dumps(analysis, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("definition", help="The definition of the verb to analyze")
    args = parser.parse_args()
    analyze_failure(args.definition)
