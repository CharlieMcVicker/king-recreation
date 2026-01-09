import csv
import json
import os
import argparse
from collections import defaultdict
from king_recreation.visualize_analysis import run_all_visualizations
from king_recreation.utils import get_class_sort_key

def load_csv(path):
    with open(path, mode='r', encoding='utf-8') as f:
        return list(csv.DictReader(f))

def save_csv(path, data, fieldnames):
    with open(path, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

def save_json(path, data):
    with open(path, mode='w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, sort_keys=True)

def analyze_matches():
    matches_path = 'artifacts/data/matches.csv'
    corpus_path = 'artifacts/data/corpus.csv'
    classes_path = 'data/king_classes.csv'
    
    if not os.path.exists(matches_path):
        print(f"Error: {matches_path} not found.")
        return
    if not os.path.exists(corpus_path):
        print(f"Error: {corpus_path} not found.")
        return
    if not os.path.exists(classes_path):
        print(f"Error: {classes_path} not found.")
        return

    matches = load_csv(matches_path)
    corpus = load_csv(corpus_path)
    king_classes_data = load_csv(classes_path)
    all_classes = sorted([row['class'] for row in king_classes_data if row['class']], key=get_class_sort_key)
    
    all_verbs = set(row['definition'] for row in corpus)
    total_verb_count = len(all_verbs)

    # 1. Class-wise Match Counts
    filtered_matches = {}
    for row in matches:
        verb = row['definition']
        cls = row['class']
        strictness = row['strictness']
        scope = row['scope']
        key = (verb, cls, strictness)
        
        if key not in filtered_matches:
            filtered_matches[key] = row
        else:
            if scope == 'full':
                filtered_matches[key] = row

    class_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
    for row in filtered_matches.values():
        class_counts[row['class']][row['strictness']][row['scope']] += 1

    class_match_data = []
    for cls in all_classes:
        class_match_data.append({
            'class': cls,
            'strict_ending': class_counts[cls]['strict']['ending'],
            'strict_full': class_counts[cls]['strict']['full'],
            'loose_ending': class_counts[cls]['loose']['ending'],
            'loose_full': class_counts[cls]['loose']['full']
        })
    
    output_dir = 'artifacts/reports'
    os.makedirs(output_dir, exist_ok=True)

    save_csv(os.path.join(output_dir, 'class_match_counts.csv'), class_match_data, 
             ['class', 'strict_ending', 'strict_full', 'loose_ending', 'loose_full'])

    # 2. Verb Coverage Summary
    coverage_summary = {}
    combos = [
        ('strict', 'full'),
        ('loose', 'full'),
        ('strict', 'ending'),
        ('loose', 'ending')
    ]

    for strictness, scope_target in combos:
        verb_match_counts = defaultdict(int)
        for key, row in filtered_matches.items():
            verb, cls, s = key
            if s == strictness:
                if scope_target == 'full':
                    if row['scope'] == 'full':
                        verb_match_counts[verb] += 1
                else: 
                    if row['scope'] == 'ending' or row['scope'] == 'full':
                        verb_match_counts[verb] += 1
        
        matched_verbs = set(verb_match_counts.keys())
        zero = len(all_verbs - matched_verbs)
        one = 0
        multiple = 0
        for count in verb_match_counts.values():
            if count == 1:
                one += 1
            elif count > 1:
                multiple += 1
        
        coverage_summary[f"{strictness}_{scope_target}"] = {
            "0": zero,
            "1": one,
            "2+": multiple,
            "coverage_pct": round((total_verb_count - zero) / total_verb_count * 100, 1) if total_verb_count > 0 else 0.0
        }

    save_json(os.path.join(output_dir, 'verb_coverage.json'), coverage_summary)

    # 2b. Export Unmatched Verbs
    verb_forms_map = {row['definition']: row for row in corpus}
    form_fields = ['present', 'imperfective', 'perfective', 'imperative', 'infinitive']

    for strictness in ['strict', 'loose']:
        target_set = set()
        for key, row in filtered_matches.items():
            verb, cls, s = key
            if s == strictness and row['scope'] == 'full':
                target_set.add(verb)
        
        unmatched = sorted(list(all_verbs - target_set))
        unmatched_data = []
        for v in unmatched:
            data = {'verb': v}
            if v in verb_forms_map:
                for field in form_fields:
                    data[field] = verb_forms_map[v].get(field, '')
            unmatched_data.append(data)
            
        save_csv(os.path.join(output_dir, f'unmatched_verbs_{strictness}.csv'), unmatched_data, ['verb'] + form_fields)

    # Print summary to console
    print("\nVerb Class Coverage Summary:")
    print(f"{'Match Configuration':<20} | {'Count (>=1)':<12} | {'Percentage':<10}")
    print("-" * 48)
    for key in sorted(coverage_summary.keys()):
        stats = coverage_summary[key]
        matched = total_verb_count - stats['0']
        pct = stats['coverage_pct']
        print(f"{key:<20} | {matched:<12} | {pct:>9}%")
    print("")

    # 3. Class Near-Miss Analysis
    near_miss_data = []
    forms = ['present', 'imperfective', 'perfective', 'imperative', 'infinitive']
    
    near_miss_groups = defaultdict(list)
    for row in filtered_matches.values():
        if row['scope'] == 'ending':
            near_miss_groups[(row['class'], row['strictness'])].append(row)
            
    # Include all classes and both strictness levels
    for cls in all_classes:
        for s in ['strict', 'loose']:
            group = near_miss_groups[(cls, s)]
            match_count = len(group)
            rates = {}
            for form in forms:
                if match_count > 0:
                    col = f'stem_final_match_{form}'
                    passed = sum(1 for r in group if r[col].lower() == 'true')
                    rate = round(passed / match_count, 3)
                else:
                    rate = 0.0
                rates[f'{form}_rate'] = rate
                
            data_row = {
                'class': cls,
                'strictness': s,
                'match_count': match_count,
                **rates
            }
            near_miss_data.append(data_row)

    # Sort near_miss_data by class (custom key) then strictness
    near_miss_data.sort(key=lambda x: (get_class_sort_key(x['class']), x['strictness']))

    save_csv(os.path.join(output_dir, 'class_near_misses.csv'), near_miss_data,
             ['class', 'strictness', 'match_count'] + [f'{f}_rate' for f in forms])

    print(f"Analysis complete. Artifacts generated in {output_dir}/")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze match data.")
    parser.add_argument("--visualize", action="store_true", help="Run visualization.")
    args = parser.parse_args()
    
    analyze_matches()
    
    if args.visualize:
        run_all_visualizations()
