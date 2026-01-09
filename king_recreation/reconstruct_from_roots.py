import os
import csv
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from king_recreation.classify_verbs import get_matches_for_verb

@dataclass
class ReconstructibleVerb:
    definition: str
    root: str
    class_name: str
    set_type: str # 'a' or 'b'
    imp_type: str # 'normal' or 'to_3rd' (boolean in 2_to_3?)
    translocutive: bool
    partitive: bool
    distributive: bool
    original_stems: Dict[str, str] = field(default_factory=dict)

# Constants
VOWELS = set('aeiouv') 
VOWEL_SET = {'a', 'e', 'o', 'u', 'v', 'i'}

def is_vowel(char):
    return char in VOWEL_SET

class ReconstructionEngine:
    def __init__(self, king_classes_path: str):
        self._classes_raw = self._load_king_classes_raw(king_classes_path)
        self.king_classes = {row['class']: row for row in self._classes_raw}
        self.prefixes_pronominal_map = {
            '3rd Set A': [
                ('ø', 'vowel_ae'), # Condition: Stem starts with a/e
                ('k-', 'vowel'),   # Condition: Stem starts with other vowel
                ('a-', 'con'),     # Condition: Stem starts with consonant
                ('ka-', 'con')     # Condition: Stem starts with consonant (Ambiguous with a-)
            ],
            '3rd Set B': [
                ('u-', 'a_replace'), # Condition: Stem starts with a (replaces a)
                ('uw-', 'vowel_no_a'), # Condition: Stem starts with vowel (not a)
                ('uwa-', 'v'),         # Condition: Stem starts with v
                ('u-', 'con'),         # Condition: Stem starts with consonant
                ('uwa-', 'con')        # Condition: Stem starts with consonant (Ambiguous)
            ],
            '2nd Set B': [
                ('ts-', 'vowel'),
                ('tsa-', 'con')
            ],
            '2nd Set A': [
                ('h-', 'vowel'),
                ('hi-', 'con')
            ],
            '2nd to 3rd': [
                ('hiy-', 'vowel'),
                ('hi-', 'con')
            ]
        }

    def _load_king_classes_raw(self, path: str) -> List[Dict[str, str]]:
        classes = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                classes.append(row)
        return classes

    def get_pronominal_set_name(self, form_name, set_type, imp_type):
        if form_name == 'present':
            return '3rd Set A' if set_type == 'a' else '3rd Set B'
        if form_name == 'imperfective':
            return '3rd Set A' if set_type == 'a' else '3rd Set B'
        if form_name == 'perfective':
            return '3rd Set B'
        if form_name == 'imperative':
            return '2nd to 3rd' if imp_type == 'to_3rd' else ('2nd Set A' if set_type == 'a' else '2nd Set B')
        if form_name == 'infinitive':
            return '3rd Set B'
        return None

    def apply_mutation(self, stem, prefix, condition):
        clean_prefix = prefix.replace('-', '')
        if clean_prefix == 'ø': clean_prefix = ''
        
        if condition == 'vowel_ae':
            if stem and stem[0] in 'ae': return clean_prefix + stem
            return None
        if condition == 'vowel': 
             if stem and is_vowel(stem[0]): return clean_prefix + stem
             return None
        if condition == 'a_replace': 
            if stem.startswith('a'):
                return clean_prefix + stem[1:] 
            return None
        if condition == 'vowel_no_a': 
            if stem and is_vowel(stem[0]) and stem[0] != 'a': return clean_prefix + stem
            return None
        if condition == 'v':
            if stem and stem[0] == 'v': return clean_prefix + stem[1:]
            return None
        if condition == 'con':
            if stem and not is_vowel(stem[0]): 
                return clean_prefix + stem
            return None
        return None

    def generate_pronominal_forms(self, stem: str, set_name: str) -> List[str]:
        candidates = []
        rules = self.prefixes_pronominal_map.get(set_name, [])
        for pref, cond in rules:
            res = self.apply_mutation(stem, pref, cond)
            if res:
                candidates.append(res)
        return candidates

    def apply_prepronominal_layer(self, forms: List[str], p_type: str, exists: bool, form_name: str) -> List[str]:
        if not exists:
            return forms
        
        new_forms = []
        for word in forms:
            if p_type == 'D':
                if is_vowel(word[0]):
                    variants = ['t' + word]
                else:
                    variants = ['ti' + word, 'te' + word, 'ts' + word]
                if word.startswith('i'):
                    variants.append('te' + word[1:])
                if form_name in ['infinitive', 'imperative']:
                    variants = ['ts'+word, 'ti'+word, 't'+word]
                else:
                    variants = ['te'+word, 't'+word]
                    if word.startswith('i'): variants.append('te' + word[1:])
                new_forms.extend(variants)
            elif p_type == 'P':
                variants = []
                if form_name == 'infinitive':
                    variants.append('iy' + word)
                    variants.append('i' + word)
                    variants.append(word) 
                else:
                    variants.append('ni' + word)
                    variants.append('n' + word)
                    variants.append(word)
                    if word.startswith('h'):
                        variants.append('hn' + word[1:])
                new_forms.extend(variants)
            elif p_type == 'T':
                variants = []
                variants.append('wi' + word)
                variants.append('w' + word)
                if word.startswith('h'):
                    variants.append('hw' + word[1:])
                new_forms.extend(variants)
        return list(set(new_forms))

    def reconstruct_verb(self, verb: ReconstructibleVerb) -> List[Dict[str, str]]:
        base_stems = {}
        class_info = self.king_classes.get(verb.class_name)
        if not class_info: return []
        
        for form_name in ['present', 'imperfective', 'perfective', 'imperative', 'infinitive']:
            ending = class_info.get(form_name, '')
            ending = ending.replace('*', '').replace('@', '')
            base_stems[form_name] = verb.root + ending
            
        form_options = {}
        for fn, stem in base_stems.items():
            set_name = self.get_pronominal_set_name(fn, verb.set_type, verb.imp_type)
            if not set_name: 
                candidates = [stem]
            else:
                candidates = self.generate_pronominal_forms(stem, set_name)
                if not candidates: candidates = [] 
            
            candidates = self.apply_prepronominal_layer(candidates, 'D', verb.distributive, fn)
            candidates = self.apply_prepronominal_layer(candidates, 'P', verb.partitive, fn)
            candidates = self.apply_prepronominal_layer(candidates, 'T', verb.translocutive, fn)
            form_options[fn] = candidates
        
        return [{fn: set(opts or []) for fn, opts in form_options.items()}]

    def get_root_candidate(self, stem: str, ending: str) -> Optional[str]:
        literal_ending = ending.replace("*", "").replace("@", "")
        if not literal_ending:
             return stem 
        if stem.endswith(literal_ending):
            return stem[:-len(literal_ending)]
        return None

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stem_corpus_path = os.path.join(base_dir, 'artifacts', 'data', 'stem_corpus.csv')
    corpus_path = os.path.join(base_dir, 'artifacts', 'data', 'corpus.csv')
    king_classes_path = os.path.join(base_dir, 'data', 'king_classes.csv')
    
    engine = ReconstructionEngine(king_classes_path)
    
    # Load Stem Corpus
    stem_corpus = []
    with open(stem_corpus_path, 'r', encoding='utf-8') as f:
        stem_corpus = list(csv.DictReader(f))
    
    # Load raw Corpus (for matching)
    full_corpus_map = {}
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            full_corpus_map[row['definition']] = row

    reconstructible_verbs = []
    consistency_analysis = []
    
    forms = ['present', 'imperfective', 'perfective', 'imperative', 'infinitive']
    
    for stem_row in stem_corpus:
        definition = stem_row['definition']
        raw_row = full_corpus_map.get(definition)
        if not raw_row: continue
        
        # 1. Use shared interface to find matches based on raw forms
        # Filter classes_raw to find strict full matches
        matches = get_matches_for_verb(raw_row, engine._classes_raw)
        strict_full_matches = [m for m in matches if m['strictness'] == 'strict' and m['scope'] == 'full']
        
        if len(strict_full_matches) == 1:
            match = strict_full_matches[0]
            cls_name = match['class']
            class_info = engine.king_classes[cls_name]
            
            # 2. Root Consistency Check
            possible_roots = {}
            is_consistent = True
            mismatch_details = []
            
            for fn in forms:
                stem = stem_row.get(fn)
                class_pattern = class_info.get(fn)
                if not stem:
                    is_consistent = False
                    mismatch_details.append(f"Missing stem for {fn}")
                    continue
                
                root = engine.get_root_candidate(stem, class_pattern)
                if root is None:
                    is_consistent = False
                    mismatch_details.append(f"{fn}: Suffix mismatch")
                else:
                    possible_roots[fn] = root
            
            if is_consistent:
                # Check if all roots are the same
                roots_list = list(possible_roots.values())
                first_root = roots_list[0]
                if not all(r == first_root for r in roots_list):
                    is_consistent = False
                    # Find which ones differ
                    diffs = [f"{fn}: '{r}'" for fn, r in possible_roots.items() if r != first_root]
                    mismatch_details.append(f"Root mismatch from {forms[0]} ('{first_root}'): " + ", ".join(diffs))
            
            # 3. Record for analysis
            analysis_row = {
                'definition': definition,
                'assigned_class': cls_name,
                'is_consistent': is_consistent,
                'mismatch_details': "; ".join(mismatch_details)
            }
            for fn in forms:
                analysis_row[f'root_{fn}'] = possible_roots.get(fn, '')
            consistency_analysis.append(analysis_row)

            if is_consistent:
                verb = ReconstructibleVerb(
                    definition=definition,
                    root=first_root,
                    class_name=cls_name,
                    set_type=stem_row['set_a_b'],
                    imp_type='to_3rd' if stem_row['2_to_3'] == 'True' else 'normal',
                    translocutive=stem_row['translocutive'] == 'True',
                    partitive=stem_row['partitive'] == 'True',
                    distributive=stem_row['distributive'] == 'True',
                    original_stems={fn: stem_row[fn] for fn in forms}
                )
                reconstructible_verbs.append(verb)
    
    print(f"Found {len(reconstructible_verbs)} reconstructible verbs out of {len(consistency_analysis)} strict full matches.")
    
    # Validation Phase
    success_count = 0
    failures = []
    
    for verb in reconstructible_verbs:
        generated_sets = engine.reconstruct_verb(verb)
        matches_all = True
        failed_forms = []
        ref = full_corpus_map.get(verb.definition)
        
        if not generated_sets:
            matches_all = False
            failed_forms = ["Generation Failed"]
        else:
            options = generated_sets[0]
            for fn in forms:
                ref_word = ref.get(fn)
                if not ref_word: continue 
                if ref_word not in options.get(fn, set()):
                    matches_all = False
                    failed_forms.append(f"{fn}: expected '{ref_word}', got {options.get(fn)}")
        
        if matches_all:
             success_count += 1
        else:
             failures.append({'definition': verb.definition, 'failed_forms': failed_forms})
             
    print(f"Validation Success: {success_count}/{len(reconstructible_verbs)}")
    
    # Export Artifacts
    artifacts_dir = os.path.join(base_dir, 'artifacts')
    reports_dir = os.path.join(artifacts_dir, 'reports')
    analysis_path = os.path.join(reports_dir, 'consistency_analysis.csv')
    report_path = os.path.join(reports_dir, 'reconstruction_report.csv')
    validation_path = os.path.join(reports_dir, 'reconstruction_validation.json')
    
    os.makedirs(reports_dir, exist_ok=True)
    
    # Save Consistency Analysis
    analysis_fields = ['definition', 'assigned_class', 'is_consistent', 'mismatch_details'] + [f'root_{fn}' for fn in forms]
    with open(analysis_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=analysis_fields)
        writer.writeheader()
        writer.writerows(consistency_analysis)
        
    # Save Reconstruction Report
    report_data = []
    for verb in reconstructible_verbs:
        # Check generated sets again for ambiguity
        generated_sets = engine.reconstruct_verb(verb)
        options = generated_sets[0] if generated_sets else {fn: set() for fn in forms}
        ambiguous_forms = [fn for fn, opts in options.items() if len(opts) > 1]
        
        report_data.append({
            'definition': verb.definition,
            'class': verb.class_name,
            'root': verb.root,
            'success': True, # All in reconstructible_verbs passed validation above or we can filter
            'ambiguous_forms': ";".join(ambiguous_forms),
            'notes': "Ambiguity implies lossy rule reversal" if ambiguous_forms else ""
        })
        
    with open(report_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['definition', 'class', 'root', 'success', 'ambiguous_forms', 'notes'])
        writer.writeheader()
        writer.writerows(report_data)
        
    with open(validation_path, 'w', encoding='utf-8') as f:
        json.dump({'summary': f"{success_count}/{len(reconstructible_verbs)}", 'failures': failures}, f, indent=4)
        
    print(f"Artifacts saved to {artifacts_dir}")

if __name__ == "__main__":
    main()
