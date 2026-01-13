import os
import csv
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from king_recreation.classify_verbs import get_matches_for_verb
from king_recreation.phonology_data import (
    Condition, VOWEL_SET, get_pronominal_set_name, 
    PronominalConfig, PrePronominalConfig, VerbConfig, StemType, MetathesisStrategy,
    get_prefix_details, attach_prefix, apply_prepronominal, is_h_dropping_set, drop_first_h
)
from king_recreation.stem_analysis import get_root_candidate, check_root_consistency

@dataclass
class ReconstructibleVerb:
    definition: str
    root: str
    class_name: str
    config: VerbConfig
    original_stems: Dict[str, str] = field(default_factory=dict)

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

    def generate_pronominal_forms(self, stem: str, set_name: str, config: PronominalConfig) -> List[str]:
        prefix, condition = get_prefix_details(set_name, config)
        
        stems_to_try = [(stem, False)]
        if is_h_dropping_set(set_name):
            dropped_stem = drop_first_h(stem)
            if dropped_stem != stem:
                stems_to_try.append((dropped_stem, True))
            
        candidates = []
        for s, dropped in stems_to_try:
            res = attach_prefix(s, prefix, condition)
            if res:
                candidates.append(res)
        return candidates

    def reconstruct_verb(self, verb: ReconstructibleVerb) -> List[Dict[str, str]]:
        base_stems = {}
        class_info = self.king_classes.get(verb.class_name)
        if not class_info: return []
        
        for form_name in ['present', 'imperfective', 'perfective', 'imperative', 'infinitive']:
            ending_pattern = class_info.get(form_name, '')
            root = verb.root
            literal_ending = ending_pattern.replace('*', '').replace('@', '')
            
            modified_root = root
            if '*' in ending_pattern:
                if len(modified_root) >= 1: modified_root = modified_root[:-1]
            elif '@' in ending_pattern:
                if len(modified_root) >= 2: modified_root = modified_root[:-2]
            
            base_stems[form_name] = modified_root + literal_ending
            
        form_options = {}
        for fn, stem in base_stems.items():
            set_name = get_pronominal_set_name(fn, verb.config.pron)
            if not set_name: 
                candidates = [stem]
            else:
                candidates = self.generate_pronominal_forms(stem, set_name, verb.config.pron)
            
            # Apply Prepronominals
            layered_candidates = []
            for c in candidates:
                layered_candidates.extend(apply_prepronominal(c, verb.config.pre, fn))
            
            form_options[fn] = layered_candidates
        
        return [{fn: set(opts or []) for fn, opts in form_options.items()}]

def main(classes_path=None):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stem_corpus_path = os.path.join(base_dir, 'artifacts', 'data', 'stem_corpus.csv')
    corpus_path = os.path.join(base_dir, 'artifacts', 'data', 'corpus.csv')
    if classes_path is None:
        king_classes_path = os.path.join(base_dir, 'data', 'king_classes.csv')
    else:
        king_classes_path = classes_path
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
            from king_recreation.phonology_data import StemType, MetathesisStrategy
            
            pre_config = PrePronominalConfig(
                translocutive=stem_row['translocutive'] == 'True',
                partitive=stem_row['partitive'] == 'True',
                distributive=stem_row['distributive'] == 'True'
            )
            pron_config = PronominalConfig(
                set_type=stem_row['set_a_b'],
                stem_type=StemType(stem_row['stem_type']),
                metathesis_strategy=MetathesisStrategy(stem_row['metathesis_strategy']),
                use_ka_variant=stem_row['ka_variant'] == 'True',
                use_uwa_for_3rd_set_b=stem_row['uwa_3rd'] == 'True',
                use_aki_for_1st_set_b=stem_row['aki_1st'] == 'True',
                use_3rd_person_object=stem_row['3rd_person_object'] == 'True'
            )
            
            verb = ReconstructibleVerb(
                definition=definition,
                root=root,
                class_name=cls_name,
                config=VerbConfig(pre=pre_config, pron=pron_config),
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
    import argparse
    parser = argparse.ArgumentParser(description="Reconstruct verbs from roots.")
    parser.add_argument("--classes", help="Path to classes CSV file")
    args = parser.parse_args()
    main(args.classes)
