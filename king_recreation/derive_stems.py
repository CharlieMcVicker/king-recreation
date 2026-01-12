import os
import csv
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional, Tuple
from king_recreation.phonology_data import Condition, VOWEL_SET, PRONOMINAL_PREFIXES_MAP, get_pronominal_set_name, is_h_dropping_set, drop_first_h

@dataclass
class Derivation:
    set_type: str  # 'Set A' or 'Set B'
    imp_type: str  # 'normal' or 'to_3rd'
    translocutive: bool
    partitive: bool
    distributive: bool
    metathesis: bool
    stems: Dict[str, str]
    stem_initial: str

def is_strict_compatible(s1: str, s2: str) -> bool:
    if s1 == s2: return True
    if s1.startswith(s2) or s2.startswith(s1): return True
    # Allow mismatch if they share a significant common prefix
    # e.g. ehlatitoh vs ehlatitol
    common_len = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2: common_len += 1
        else: break
    return common_len >= 3 or common_len == min(len(s1), len(s2))

def is_loose_compatible(s1: str, s2: str) -> bool:
    # Stem consistency should be checked between all forms for starting sound
    return bool(s1 and s2 and s1[0] == s2[0])

# Backwards compatibility for other modules if needed (though we should update them)
is_compatible = is_strict_compatible

class StemDeriver:
    def __init__(self):
        self.vowels = VOWEL_SET
        # Pre-compute or cache things if needed

    def is_vowel(self, char):
        return char in self.vowels

    def match_prepronominal(self, word, exists, p_type, form_name):
        if not exists:
            return [('', word)]
        
        matches = []
        # Translocutive
        if p_type == 'T':
            if word.startswith('w'):
                if len(word) > 1 and word[1] == 'i':
                    matches.append(('wi-', word[2:]))
                else:
                    matches.append(('w-', word[1:]))
            if word.startswith('hw'):
                matches.append(('hw-', 'h' + word[2:])) # h reinserted
        
        # Partitive
        elif p_type == 'P':
            if form_name == 'infinitive':
                if word.startswith('iy'): matches.append(('iy-', word[2:]))
                if word.startswith('i'): matches.append(('i-', word[1:]))
                if word.startswith('i'): matches.append(('', word)) # ø before -i
            else:
                if word.startswith('n'):
                    if len(word) > 1 and word[1] == 'i':
                        matches.append(('ni-', word[2:]))
                    else:
                        matches.append(('n-', word[1:]))
                if word.startswith('hn'):
                    matches.append(('hn-', 'h' + word[2:])) # h reinserted
                
                # Partitive ø rule: Before a stem or pronoun starting with -i
                if word.startswith('i'):
                    matches.append(('', word)) 
        
        # Distributive
        elif p_type == 'D':
            if form_name in ['infinitive', 'imperative']:
                if word.startswith('ts'): matches.append(('ts-', word[2:]))
                if word.startswith('ti'): matches.append(('ti-', word[2:]))
                if word.startswith('t'): matches.append(('t-', word[1:]))
            else:
                if word.startswith('te'): 
                    matches.append(('te-', word[2:]))
                    matches.append(('te-', 'i' + word[2:])) # te- replaces -i
                if word.startswith('t'): matches.append(('t-', word[1:]))
        
        return matches

    def extract_literals(self, forms, set_type, imp_type, t, p, d):
        """
        Extracts literal stems for all forms under the given configuration.
        Returns a dict: {form_name: Set[(stem_string, uses_metathesis)]}
        Returns None if any form fails to produce a valid stem (which invalidates the config).
        """
        literals = {}
        
        for fn, word in forms.items():
            form_literals = set()
            
            # Step 1: Prepronominal T -> P -> D
            current_words = [('', word)]
            for exists, p_type in [(t, 'T'), (p, 'P'), (d, 'D')]:
                next_words = []
                for _, w in current_words:
                    next_words.extend(self.match_prepronominal(w, exists, p_type, fn))
                current_words = list(set(next_words)) # Unique versions

            # Step 2: Pronominal
            pron_type = get_pronominal_set_name(fn, set_type, imp_type)
            prefixes = PRONOMINAL_PREFIXES_MAP[pron_type]
            is_h_drop = is_h_dropping_set(pron_type)

            for _, w in current_words:
                for pref, cond in prefixes:
                    uses_meta = False
                    candidate = None
                    
                    if pref == 'ø':
                        if w and cond == Condition.VOWEL_AE and w[0] in 'ae':
                            candidate = w
                    elif w.startswith(pref.replace('-', '')):
                        remainder = w[len(pref.replace('-', '')):]
                        
                        # Condition validation
                        is_valid = True
                        if cond == Condition.VOWEL:
                            is_valid = remainder and self.is_vowel(remainder[0])
                        elif cond == Condition.CONSONANT:
                            # In h-dropping sets, literal remainder might be vowel (h dropped).
                            # So we allow vowel matches in h-drop sets.
                            is_valid = remainder and (not self.is_vowel(remainder[0]) or is_h_drop)
                        elif cond == Condition.VOWEL_AE:
                            is_valid = remainder and remainder[0] in 'ae'
                        elif cond == Condition.VOWEL_NO_A:
                            is_valid = remainder and self.is_vowel(remainder[0]) and remainder[0] != 'a'
                        
                        if not is_valid:
                            continue

                        # Special rules for Set B u- replaces a
                        if cond == Condition.A_REPLACE:
                            candidate = 'a' + remainder
                        elif cond == Condition.V and pref == 'uwa-':
                            candidate = 'v' + remainder
                        elif cond == Condition.ASPIRATED and remainder.startswith('th'):
                             candidate = remainder
                        elif cond == Condition.S_STEM and remainder.startswith('s'):
                             candidate = remainder
                        elif cond == Condition.METATHESIS_H_CONS:
                             # Restore 'h' -> 'hnogi'
                             candidate = 'h' + remainder
                             uses_meta = True
                        elif cond == Condition.METATHESIS_VOWEL:
                             # Restore h after first vowel: 'ehlatitoh'
                             if remainder:
                                 v = remainder[0]
                                 candidate = v + 'h' + remainder[1:]
                                 uses_meta = True
                        else:
                            # Standard case
                            candidate = remainder
                    
                    if candidate is not None:
                        form_literals.add((candidate, uses_meta))
            
            if not form_literals:
                return None # This form could not be parsed with this config
            
            literals[fn] = form_literals
            
        return literals

    def derive_row(self, row: Dict[str, str]) -> List[Derivation]:
        form_names = ['present', 'present_1sg', 'imperfective', 'perfective', 'imperative', 'infinitive']
        forms = {fn: row[fn] for fn in form_names if row.get(fn)}
        if not forms: return []

        valid_derivations = []
        for set_type in ['Set A', 'Set B']:
            for imp_type in ['normal', 'to_3rd']:
                for t in [True, False]:
                    for p in [True, False]:
                        for d in [True, False]:
                            literals = self.extract_literals(forms, set_type, imp_type, t, p, d)
                            if not literals: continue
                            
                            # Identify Candidate Consensus Stems
                            # Use stems derived from non-h-dropping forms as Target Stems
                            candidates = set()
                            
                            for fn, form_literals in literals.items():
                                pron_type = get_pronominal_set_name(fn, set_type, imp_type)
                                if not is_h_dropping_set(pron_type):
                                    for s, meta in form_literals:
                                        candidates.add(s)
                            
                            # Fallback: if no non-h-dropping forms (unlikely), try all literals
                            if not candidates:
                                for fn, form_literals in literals.items():
                                    for s, meta in form_literals:
                                        candidates.add(s)
                            
                            # Validate Candidates
                            for target in candidates:
                                explained_all = True
                                final_stems = {}
                                metathesis_involved = False
                                
                                for fn in forms:
                                    pron_type = get_pronominal_set_name(fn, set_type, imp_type)
                                    is_h_drop = is_h_dropping_set(pron_type)
                                    
                                    # Check if target explains this form
                                    matched_literal = False
                                    best_match = None
                                    
                                    # Strictness Logic
                                    # "stem consistency should be checked between all forms for starting sound" (Loose)
                                    # "and between pres and 1st pres for matching" (Strict)
                                    use_strict = (fn in ['present', 'present_1sg'])

                                    # Collect all valid matches for this form to pick the best one
                                    valid_matches = [] # List of (stem, metathesis_bool, is_dropped_h)

                                    # Check direct match
                                    for s, meta in literals[fn]:
                                        is_valid = False
                                        if use_strict:
                                            if is_strict_compatible(s, target): is_valid = True
                                        else:
                                            if is_loose_compatible(s, target): is_valid = True
                                        
                                        if is_valid:
                                            valid_matches.append((s, meta, False))

                                    
                                    # If h-drop set, check drop_first_h
                                    if is_h_drop:
                                        dropped = drop_first_h(target)
                                        for s, meta in literals[fn]:
                                            is_valid = False
                                            if use_strict:
                                                if is_strict_compatible(s, dropped): is_valid = True
                                            else:
                                                if is_loose_compatible(s, dropped): is_valid = True
                                            
                                            if is_valid:
                                                valid_matches.append((s, meta, True)) # True = is_dropped match
                                    
                                    if valid_matches:
                                        matched_literal = True
                                        # Pick the best match
                                        # Criteria:
                                        # 1. Longest common prefix with target (prefer matches that overlap more)
                                        # 2. Prefer direct match over dropped match? (Maybe not strictly, score should handle it)
                                        
                                        def score_match(m):
                                            s, meta, dropped = m
                                            # Calculate overlap with target
                                            # If dropped match, we are comparing s to dropped(target).
                                            # But we want to see how "good" s is relative to target.
                                            # Let's compare s to target directly for scoring?
                                            # Or compare s to the thing it matched (target or dropped).
                                            
                                            ref = drop_first_h(target) if dropped else target
                                            
                                            common = 0
                                            for c1, c2 in zip(s, ref):
                                                if c1 == c2: common += 1
                                                else: break
                                            return common
                                        
                                        # Sort by score descending
                                        valid_matches.sort(key=score_match, reverse=True)
                                        best_match_tuple = valid_matches[0]
                                        
                                        best_match = best_match_tuple[0]
                                        if best_match_tuple[1]: metathesis_involved = True
                                    
                                    if not matched_literal:
                                        explained_all = False
                                        break
                                    
                                    # We use the actual matched literal for the output to preserve suffixes
                                    final_stems[fn] = best_match
                                
                                if explained_all:
                                    valid_derivations.append(Derivation(
                                        set_type=set_type,
                                        imp_type=imp_type,
                                        translocutive=t,
                                        partitive=p,
                                        distributive=d,
                                        metathesis=metathesis_involved,
                                        stems=final_stems,
                                        stem_initial=target[0] if target else ''
                                    ))

        return valid_derivations

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, 'artifacts', 'data', 'corpus.csv')
    output_path = os.path.join(base_dir, 'artifacts', 'data', 'stem_corpus.csv')
    failures_path = os.path.join(base_dir, 'artifacts', 'reports', 'stem_derivation_failures.csv')

    deriver = StemDeriver()
    labeled_data = []
    failures = []

    with open(input_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            derivations = deriver.derive_row(row)
            if not derivations:
                failures.append(row)
            else:
                # Use the first valid derivation for labeling
                # Ideally we would prioritize or disambiguate
                # Sorting by some heuristic could help
                
                # Deduplicate derivations (sometimes multiple targets are same or similar)
                # For now just take first
                d = derivations[0]
                
                # Overwrite form columns with cleaned stems (Consensus Stems)
                for fn, stem in d.stems.items():
                    row[fn] = stem
                
                row['set_a_b'] = 'a' if d.set_type == 'Set A' else 'b'
                row['2_to_3'] = str(d.imp_type == 'to_3rd')
                row['translocutive'] = str(d.translocutive)
                row['partitive'] = str(d.partitive)
                row['distributive'] = str(d.distributive)
                row['metathesis'] = str(d.metathesis)
                row['multiple_explanations'] = str(len(derivations) > 1)
                labeled_data.append(row)

    if labeled_data:
        keys = labeled_data[0].keys()
        with open(output_path, 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(labeled_data)

    if failures:
        keys = failures[0].keys()
        with open(failures_path, 'w', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(failures)

    print(f"Processed {len(labeled_data) + len(failures)} rows.")
    print(f"Success: {len(labeled_data)}")
    print(f"Failures: {len(failures)}")

if __name__ == "__main__":
    main()