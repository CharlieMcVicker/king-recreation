import os
import csv
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional, Tuple

@dataclass
class Derivation:
    set_type: str  # 'Set A' or 'Set B'
    imp_type: str  # 'normal' or 'to_3rd'
    translocutive: bool
    partitive: bool
    distributive: bool
    stems: Dict[str, str]
    stem_initial: str

def get_vowel_set():
    return {'a', 'e', 'o', 'u', 'v', 'i'}

class StemDeriver:
    def __init__(self):
        self.vowels = get_vowel_set()
        self.prefixes_pronominal = {
            '3rd Set A': [('ø', 'vowel_ae'), ('k-', 'vowel'), ('a-', 'con'), ('ka-', 'con')],
            '3rd Set B': [('u-', 'a_replace'), ('uw-', 'vowel_no_a'), ('uwa-', 'v'), ('u-', 'con'), ('uwa-', 'con')],
            '2nd Set B': [('ts-', 'vowel'), ('tsa-', 'con')],
            '2nd Set A': [('h-', 'vowel'), ('hi-', 'con')],
            '2nd to 3rd': [('hiy-', 'vowel'), ('hi-', 'con')]
        }

    def is_vowel(self, char):
        return char in self.vowels

    def get_pronominal_prefix(self, form_name, set_type, imp_type):
        if form_name == 'present':
            return '3rd Set A' if set_type == 'Set A' else '3rd Set B'
        if form_name == 'imperfective':
            return '3rd Set A' if set_type == 'Set A' else '3rd Set B'
        if form_name == 'perfective':
            return '3rd Set B'
        if form_name == 'imperative':
            return '2nd to 3rd' if imp_type == 'to_3rd' else ('2nd Set A' if set_type == 'Set A' else '2nd Set B')
        if form_name == 'infinitive':
            return '3rd Set B'
        return None

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

    def derive_row(self, row: Dict[str, str]) -> List[Derivation]:
        form_names = ['present', 'imperfective', 'perfective', 'imperative', 'infinitive']
        forms = {fn: row[fn] for fn in form_names if row[fn]}
        if not forms: return []

        valid_derivations = []
        for set_type in ['Set A', 'Set B']:
            for imp_type in ['normal', 'to_3rd']:
                for t in [True, False]:
                    for p in [True, False]:
                        for d in [True, False]:
                            deriv = self.test_config(forms, set_type, imp_type, t, p, d)
                            if deriv:
                                valid_derivations.append(deriv)
        return valid_derivations

    def test_config(self, forms, set_type, imp_type, t, p, d):
        possible_stems = {fn: [] for fn in forms}
        
        for fn, word in forms.items():
            # Step 1: Prepronominal T -> P -> D
            current_words = [('', word)]
            for exists, p_type in [(t, 'T'), (p, 'P'), (d, 'D')]:
                next_words = []
                for _, w in current_words:
                    next_words.extend(self.match_prepronominal(w, exists, p_type, fn))
                current_words = list(set(next_words)) # Unique versions

            # Step 2: Pronominal
            pron_type = self.get_pronominal_prefix(fn, set_type, imp_type)
            prefixes = self.prefixes_pronominal[pron_type]
            
            for _, w in current_words:
                for pref, cond in prefixes:
                    if pref == 'ø':
                        if w and cond == 'vowel_ae' and w[0] in 'ae':
                            possible_stems[fn].append(w)
                    elif w.startswith(pref.replace('-', '')):
                        remainder = w[len(pref.replace('-', '')):]
                        # Special rules for Set B u- replaces a
                        if cond == 'a_replace':
                            possible_stems[fn].append('a' + remainder)
                        elif cond == 'v' and pref == 'uwa-':
                            possible_stems[fn].append('v' + remainder)
                        else:
                            possible_stems[fn].append(remainder)
                            # Handle /h/ alternation for 2->3 forms: restore dropped /h/
                            if pron_type == '2nd to 3rd':
                                possible_stems[fn].append('h' + remainder)

        # Cross-form check: intersection of all stem possibilities
        # Skip forms that are missing
        for fn, stems in possible_stems.items():
            if fn in forms and not stems:
                return None
        
        # Simple consistency check for now: constant stem initial and same prefix variant usage if possible
        # This is strictly about finding ONE shared stem string that could be extracted
        # The prompt says: "Present Stem: the present tense form with... prefixes removed"
        # "Should have the right stem initial that matches other forms"
        
        common_stems = set(possible_stems['present'])
        for fn in possible_stems:
            # Stems might differ after the first character, but we need consistent initial
            # Actually, per prompt "All forms... have the same stem-initial sound"
            # It's better to find if there is a consistent mapping.
            pass

        # For MVP: find stems in 'present' where the initial char is consistent with at least one possible stem in all other forms
        valid_present_stems = []
        for ps in possible_stems['present']:
            if not ps: continue
            initial = ps[0]
            consistent = True
            for fn, p_stems in possible_stems.items():
                if fn not in forms: continue
                if not any(s and s[0] == initial for s in p_stems):
                    consistent = False
                    break
            if consistent:
                valid_present_stems.append(ps)
        
        if valid_present_stems:
            final_stems = {}
            # For each form, pick the stems that match the consistent initial
            # Use the first valid present stem as the reference for disambiguation
            ref_stem = valid_present_stems[0]
            initial = ref_stem[0]

            for fn in possible_stems:
                if fn not in forms: continue
                matching_stems = [s for s in possible_stems[fn] if s and s[0] == initial]
                
                # Disambiguate if we have multiple candidates (e.g. hvkhita vs hyvkhita)
                if len(matching_stems) > 1:
                    # Score by length of common prefix with reference stem
                    def prefix_score(s):
                        l = 0
                        for c1, c2 in zip(s, ref_stem):
                            if c1 == c2: l += 1
                            else: break
                        return l
                    
                    # Get scores
                    scores = getattr(self, '_memo_scores', {})
                    scored_stems = []
                    for s in matching_stems:
                        score = prefix_score(s)
                        scored_stems.append((score, s))
                    
                    # Keep only the max scored ones
                    if scored_stems:
                        max_score = max(s[0] for s in scored_stems)
                        matching_stems = [s[1] for s in scored_stems if s[0] == max_score]

                final_stems[fn] = ";".join(matching_stems)

            return Derivation(
                set_type=set_type,
                imp_type=imp_type,
                translocutive=t,
                partitive=p,
                distributive=d,
                stems=final_stems,
                stem_initial=initial
            )
        return None

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
                d = derivations[0]
                # Overwrite form columns with cleaned stems
                for fn, stem in d.stems.items():
                    row[fn] = stem
                
                row['set_a_b'] = 'a' if d.set_type == 'Set A' else 'b'
                row['2_to_3'] = d.imp_type == 'to_3rd'
                row['translocutive'] = d.translocutive
                row['partitive'] = d.partitive
                row['distributive'] = d.distributive
                row['multiple_explanations'] = len(derivations) > 1
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
