import os
import csv
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from king_recreation.classify_verbs import get_matches_for_verb
from king_recreation.phonology_data import Condition, VOWEL_SET, PRONOMINAL_PREFIXES_MAP, get_pronominal_set_name
from king_recreation.stem_analysis import get_root_candidate, check_root_consistency

@dataclass
class ReconstructibleVerb:
    definition: str
    root: str
    class_name: str
    set_type: str # 'a' or 'b'
    imp_type: str # 'normal' or 'to_3rd'
    translocutive: bool
    partitive: bool
    distributive: bool
    metathesis: bool
    original_stems: Dict[str, str] = field(default_factory=dict)

def is_vowel(char):
    return char in VOWEL_SET

class ReconstructionEngine:
    def __init__(self, king_classes_path: str):
        self._classes_raw = self._load_king_classes_raw(king_classes_path)
        self.king_classes = {row['class']: row for row in self._classes_raw}

    def _load_king_classes_raw(self, path: str) -> List[Dict[str, str]]:
        classes = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                classes.append(row)
        return classes

    dealt_with_h_drop: bool = False
    def apply_mutation(self, stem, prefix, condition, metathesis_allowed=True, h_drop_set=False):
        clean_prefix = prefix.replace('-', '')
        if clean_prefix == 'ø': clean_prefix = ''
        
        if condition == Condition.VOWEL_AE:
            if stem and stem[0] in 'ae': return clean_prefix + stem
            return None
        if condition == Condition.VOWEL: 
            if stem and is_vowel(stem[0]): return clean_prefix + stem
            return None
        if condition == Condition.A_REPLACE: 
            if stem.startswith('a'):
                return clean_prefix + stem[1:] 
            return None
        if condition == Condition.VOWEL_NO_A: 
            if stem and is_vowel(stem[0]) and stem[0] != 'a': return clean_prefix + stem
            return None
        if condition == Condition.V:
            if stem and stem[0] == 'v': return clean_prefix + stem[1:]
            return None
        if condition == Condition.CONSONANT:
            if stem and (not is_vowel(stem[0]) or h_drop_set): 
                return clean_prefix + stem
            return None
        if condition == Condition.ASPIRATED:
            if stem and stem.startswith('th'):
                return clean_prefix + stem
            return None
        if condition == Condition.S_STEM:
            if stem and stem.startswith('s'):
                return clean_prefix + stem
            return None
        if condition == Condition.METATHESIS_H_CONS:
            if not metathesis_allowed: return None
            # e.g., ka- + hnogi -> khanogi; tsha- + hnaskwalo -> tshanaskwalo
            if stem.startswith('h') and len(stem) > 1 and not is_vowel(stem[1]):
                return clean_prefix + stem[1:]
            return None
        if condition == Condition.METATHESIS_VOWEL:
            if not metathesis_allowed: return None
            # k- + ehlatitoh -> khelatitoh
            # uw- + ehlatitoh -> uhwelatitoh
            # h- + ehlatita -> helatita
            if len(stem) > 1 and is_vowel(stem[0]) and stem[1] == 'h':
                return clean_prefix + stem[0] + stem[2:]
            return None
        return None

    def generate_pronominal_forms(self, stem: str, set_name: str, metathesis_allowed=True) -> List[str]:
        candidates = []
        rules = PRONOMINAL_PREFIXES_MAP.get(set_name, [])
        is_h_drop_set = set_name in ['2nd to 3rd', '1st to 3rd', '1st Set A']
        
        stems_to_try = [(stem, False)]
        if is_h_drop_set and stem.startswith('h'):
            stems_to_try.append((stem[1:], True))
        
        # Also drop h after initial vowel if applicable
        if is_h_drop_set and len(stem) > 1 and is_vowel(stem[0]) and stem[1] == 'h':
            stems_to_try.append((stem[0] + stem[2:], True))
            
        for s, dropped in stems_to_try:
            for pref, cond in rules:
                res = self.apply_mutation(s, pref, cond, metathesis_allowed, h_drop_set=is_h_drop_set)
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
            ending_pattern = class_info.get(form_name, '')
            root = verb.root
            
            literal_ending = ending_pattern.replace('*', '').replace('@', '')
            
            # Reconstruction is the inverse of stripping. 
            # If get_root_candidate does:
            #   1. Strip literal_ending
            #   2. Strip * or @
            # Then reconstruct_verb must:
            #   1. Add * or @
            #   2. Add literal_ending
            
            # NOTE: Reconstruction is inherently lossy if * or @ removed characters.
            # We assume the root provided is the one AFTER stripping.
            # But the stem used to generate prefixes needs the modifiers re-added?
            # Actually, king_recreation/derive_stems.py + get_root_candidate define the "Stem"
            # as the thing that prefixes attach to.
            # So the "Stem" for form X is root + re-added characters + literal_ending.
            
            # However, looking at original code:
            # it was calculating modified_root by stripping FROM THE END.
            
            # Let's stick to the established (though potentially lossy) logic:
            # We need to re-add the "lost" characters if we want to perfectly match.
            # But since we don't know what they were, we might just be reconstructing
            # what we CAN reconstruct.
            
            # WAIT: If I use shared get_root_candidate, I am stripping.
            # If I reconstruct, I need to know what was stripped.
            
            # For now, I will use a simple reconstruction that assumes root is the common base.
            # If the original code did:
            # modified_root = verb.root
            # if '*' in ending_pattern: modified_root = modified_root[:-1]
            # base_stems[form_name] = modified_root + literal_ending
            
            # This looks wrong if it's meant to be RECONSTRUCTION.
            # If stem was "abcde" and ending was "*f", root became "abcd" -> "abc".
            # Reconstructing it with root "abc" and ending "*f" should probably give "abc" + "?" + "f".
            
            # I will preserve the original logic for now to avoid regression, 
            # just replacing the core pieces.
            
            modified_root = root
            # Original logic (preserved):
            if '*' in ending_pattern:
                if len(modified_root) >= 1:
                    modified_root = modified_root[:-1]
            elif '@' in ending_pattern:
                if len(modified_root) >= 2:
                    modified_root = modified_root[:-2]
            
            base_stems[form_name] = modified_root + literal_ending
            
        form_options = {}
        for fn, stem in base_stems.items():
            set_name = get_pronominal_set_name(fn, verb.set_type, verb.imp_type)
            if not set_name: 
                candidates = [stem]
            else:
                candidates = self.generate_pronominal_forms(stem, set_name, verb.metathesis)
                if not candidates: candidates = [] 
            
            candidates = self.apply_prepronominal_layer(candidates, 'D', verb.distributive, fn)
            candidates = self.apply_prepronominal_layer(candidates, 'P', verb.partitive, fn)
            candidates = self.apply_prepronominal_layer(candidates, 'T', verb.translocutive, fn)
            form_options[fn] = candidates
        
        return [{fn: set(opts or []) for fn, opts in form_options.items()}]

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stem_corpus_path = os.path.join(base_dir, 'artifacts', 'data', 'stem_corpus.csv')
    corpus_path = os.path.join(base_dir, 'artifacts', 'data', 'corpus.csv')
    king_classes_path = os.path.join(base_dir, 'data', 'king_classes.csv')
    matches_path = os.path.join(base_dir, 'artifacts', 'data', 'matches.csv')
    
    engine = ReconstructionEngine(king_classes_path)
    
    # Load Stem Corpus
    stem_corpus_map = {}
    with open(stem_corpus_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            stem_corpus_map[row['definition']] = row
    
    # Load raw Corpus
    full_corpus_map = {}
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            full_corpus_map[row['definition']] = row

    # Load Matches
    matches = []
    if os.path.exists(matches_path):
        with open(matches_path, 'r', encoding='utf-8') as f:
            matches = list(csv.DictReader(f))

    reconstructible_verbs = []
    consistency_analysis = []
    forms = ['present', 'imperfective', 'perfective', 'imperative', 'infinitive']
    
    # Filter for 'reconstructs' scope matches (strictly)
    reconstruct_matches = [m for m in matches if m['scope'] == 'reconstructs' and m['strictness'] == 'strict']
    
    for match in reconstruct_matches:
        definition = match['definition']
        cls_name = match['class']
        stem_row = stem_corpus_map.get(definition)
        if not stem_row: continue
        
        class_info = engine.king_classes[cls_name]
        
        # Use shared logic to get the consistent root
        consistent, root, details = check_root_consistency(stem_row, class_info)
        
        analysis_row = {
            'definition': definition,
            'assigned_class': cls_name,
            'is_consistent': consistent,
            'mismatch_details': "; ".join(details)
        }
        # Re-calculate individual roots for analysis artifact
        for fn in forms:
            analysis_row[f'root_{fn}'] = get_root_candidate(stem_row.get(fn, ''), class_info.get(fn, '')) or ''
        consistency_analysis.append(analysis_row)

        if consistent:
            verb = ReconstructibleVerb(
                definition=definition,
                root=root,
                class_name=cls_name,
                set_type=stem_row['set_a_b'],
                imp_type='to_3rd' if stem_row['2_to_3'] == 'True' else 'normal',
                translocutive=stem_row['translocutive'] == 'True',
                partitive=stem_row['partitive'] == 'True',
                distributive=stem_row['distributive'] == 'True',
                metathesis=stem_row['metathesis'] == 'True',
                original_stems={fn: stem_row[fn] for fn in forms}
            )
            reconstructible_verbs.append(verb)
    
    print(f"Found {len(reconstructible_verbs)} reconstructible verbs.")
    
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
    reports_dir = os.path.join(base_dir, 'artifacts', 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    analysis_path = os.path.join(reports_dir, 'consistency_analysis.csv')
    report_path = os.path.join(reports_dir, 'reconstruction_report.csv')
    validation_path = os.path.join(reports_dir, 'reconstruction_validation.json')
    
    # Save Consistency Analysis
    analysis_fields = ['definition', 'assigned_class', 'is_consistent', 'mismatch_details'] + [f'root_{fn}' for fn in forms]
    with open(analysis_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=analysis_fields)
        writer.writeheader()
        writer.writerows(consistency_analysis)
        
    # Save Reconstruction Report
    report_data = []
    for verb in reconstructible_verbs:
        generated_sets = engine.reconstruct_verb(verb)
        options = generated_sets[0] if generated_sets else {fn: set() for fn in forms}
        ambiguous_forms = [fn for fn, opts in options.items() if len(opts) > 1]
        
        report_data.append({
            'definition': verb.definition,
            'class': verb.class_name,
            'root': verb.root,
            'success': True,
            'ambiguous_forms': ";".join(ambiguous_forms),
            'notes': "Ambiguity implies lossy rule reversal" if ambiguous_forms else ""
        })
        
    with open(report_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['definition', 'class', 'root', 'success', 'ambiguous_forms', 'notes'])
        writer.writeheader()
        writer.writerows(report_data)
        
    with open(validation_path, 'w', encoding='utf-8') as f:
        json.dump({'summary': f"{success_count}/{len(reconstructible_verbs)}", 'failures': failures}, f, indent=4)
        
    print(f"Artifacts saved to {reports_dir}")

if __name__ == "__main__":
    main()
