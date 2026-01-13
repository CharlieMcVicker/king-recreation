import unittest
import csv
import os
from king_recreation.derive_stems import StemDeriver, Derivation, strip_prepronominals, is_strict_compatible, is_loose_compatible, is_compatible_with_vowel_restoration
from king_recreation.phonology_data import (
    StemType, MetathesisStrategy, PronominalConfig, PrePronominalConfig,
    get_pronominal_set_name, is_h_dropping_set, drop_first_h,
    get_stem_type, get_prefix_details, detach_prefix, VOWEL_SET, Condition
)

class TestStemDerivations(unittest.TestCase):
    corpus_rows = []

    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        input_path = os.path.join(base_dir, 'artifacts', 'data', 'corpus.csv')
        if os.path.exists(input_path):
            with open(input_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                cls.corpus_rows = list(reader)
        else:
            print(f"Warning: Corpus file not found at {input_path}")

    def diagnose_derivation(self, row, target_pron, target_pre):
        print(f"\n[DIAGNOSIS] Analyzing failure for definition: '{row.get('definition')}'")
        print(f"[DIAGNOSIS] Expected Config: {target_pron}")
        if target_pre:
            print(f"[DIAGNOSIS] Expected Pre-Config: {target_pre}")
        else:
            print(f"[DIAGNOSIS] No Pre-Config enforced (trying all valid pre-configs)")
            
        form_names = ['present', 'present_1sg', 'imperfective', 'perfective', 'imperative', 'infinitive']
        forms = {fn: row[fn] for fn in form_names if row.get(fn)}
        
        potential_pre_configs = []
        if target_pre:
            potential_pre_configs.append(target_pre)
        else:
             for t in [False, True]:
                for p in [False, True]:
                    for d in [False, True]:
                        potential_pre_configs.append(PrePronominalConfig(t, p, d))
        
        successful_pre_strips = []
        for pc in potential_pre_configs:
            intermediate = strip_prepronominals(forms, pc)
            if intermediate:
                successful_pre_strips.append((pc, intermediate))
        
        if not successful_pre_strips:
            print("[DIAGNOSIS] ALL Pre-Pronominal configurations failed to strip prefixes consistently.")
            return

        print(f"[DIAGNOSIS] Found {len(successful_pre_strips)} valid Pre-Pronominal strippings. Proceeding to check Pronominal logic.")
        
        any_pron_success = False
        
        for pc, intermediate in successful_pre_strips:
            print(f"\n[DIAGNOSIS] Testing PreConfig: {pc}")
            for use_3rd in [False, True]:
                print(f"  [DIAGNOSIS] Testing use_3rd_person_object='{use_3rd}'")
                
                derived_stems = {}
                failed_prefix = False
                
                # Check consistency of target_pron with use_3rd
                # We need a new config object that merges target_pron with use_3rd for testing?
                # Actually, target_pron is passed in. If target_pron has usage_3rd fixed, we should maybe only test that?
                # But here we are diagnosing why it failed.
                
                # For diagnosis, we construct a temporary config to check prefixes
                check_config = PronominalConfig(
                    set_type=target_pron.set_type,
                    stem_type=target_pron.stem_type,
                    metathesis_strategy=target_pron.metathesis_strategy,
                    use_ka_variant=target_pron.use_ka_variant,
                    use_uwa_for_3rd_set_b=target_pron.use_uwa_for_3rd_set_b,
                    use_aki_for_1st_set_b=target_pron.use_aki_for_1st_set_b,
                    use_3rd_person_object=use_3rd
                )

                for fn, word in intermediate.items():
                    set_name = get_pronominal_set_name(fn, check_config)
                    prefix, condition = get_prefix_details(set_name, target_pron)
                    
                    stem = detach_prefix(word, prefix, condition, target_pron.metathesis_strategy)
                    
                    if stem is None:
                        print(f"    [FAILURE] Form '{fn}' ('{word}') failed to detach prefix '{prefix}' with condition {condition}")
                        failed_prefix = True
                    else:
                        print(f"    [SUCCESS] Form '{fn}' ('{word}') matches prefix '{prefix}' -> Stem: '{stem}'")
                        derived_stems[fn] = stem
                        
                if failed_prefix:
                    continue
                
                consensus_candidates = [s for fn, s in derived_stems.items() if fn != 'present_1sg']
                if not consensus_candidates: consensus_candidates = list(derived_stems.values())
                consensus_stem = consensus_candidates[0]
                
                print(f"    [INFO] Candidate Consensus Stem: '{consensus_stem}'")
                
                consensus_fail = False
                for fn, s in derived_stems.items():
                    if fn == 'present_1sg': continue
                    set_name = get_pronominal_set_name(fn, check_config)
                    is_h_drop = is_h_dropping_set(set_name)
                    ref = drop_first_h(consensus_stem) if is_h_drop else consensus_stem
                    
                    is_ok = False
                    if fn == 'present':
                        if is_strict_compatible(s, ref): is_ok = True
                        elif is_h_drop and is_compatible_with_vowel_restoration(s, ref): is_ok = True
                    else:
                        if is_loose_compatible(s, ref): is_ok = True
                    
                    if not is_ok:
                        print(f"    [FAILURE] Consensus Check Failed for '{fn}'. Derived: '{s}', Expected Ref: '{ref}'")
                        consensus_fail = True
                
                if consensus_fail:
                    continue
                    
                calc_stem_type = get_stem_type(consensus_stem)
                if calc_stem_type != target_pron.stem_type:
                    print(f"    [FAILURE] Stem Type Mismatch. Calculated: {calc_stem_type}, Expected: {target_pron.stem_type}")
                    continue
                    
                print("    [SUCCESS] Full Derivation Successful with this configuration!")
                any_pron_success = True

        if not any_pron_success:
            print("\n[DIAGNOSIS] No successful derivation found with target pronominal config.")
        
        # Check if this config is reachable by derive_row
        s_type = target_pron.set_type
        allowed_ka = [False, True] if s_type == 'a' else [False]
        allowed_uwa = [False, True]
        allowed_aki = [False, True]
        
        reachable = True
        if target_pron.use_ka_variant not in allowed_ka: reachable = False
        if target_pron.use_uwa_for_3rd_set_b not in allowed_uwa: reachable = False
        if target_pron.use_aki_for_1st_set_b not in allowed_aki: reachable = False
        
        if not reachable:
            print(f"\n[DIAGNOSIS CRITICAL WARNING] The expected configuration is NOT SEARCHED by derive_row due to set_type constraints.")
            print(f"  set_type='{s_type}' implies:")
            print(f"    allowed_ka = {allowed_ka} (Target: {target_pron.use_ka_variant})")
            print(f"    allowed_uwa = {allowed_uwa} (Target: {target_pron.use_uwa_for_3rd_set_b})")
            print(f"    allowed_aki = {allowed_aki} (Target: {target_pron.use_aki_for_1st_set_b})")
            print("  This explains why the test fails even if derivation logic succeeds above.")

    def test_regressions(self):
        """
        To add new regression tests, add tuples to the TEST_CASES list below.
        Format: (definition_string, expected_pron_config, optional_pre_config)
        Example:
        ("to speak", PronominalConfig(set_type="a", stem_type=StemType.CONSONANT))
        """
        TEST_CASES = [
            # ADD YOUR TEST CASES HERE
            # ("he's closing his eyes", PronominalConfig(set_type="a", stem_type=StemType.ASPIRATED)),
            ("he's plowing it", PronominalConfig(set_type="a", use_ka_variant=True, use_uwa_for_3rd_set_b=True, stem_type=StemType.CONSONANT)),
            ("he's breathing", PronominalConfig(set_type="a", use_ka_variant=True, stem_type=StemType.VOWEL_A, metathesis_strategy=MetathesisStrategy.VOWEL)),
            ("he's singing", PronominalConfig(set_type="a", use_ka_variant=True, stem_type=StemType.CONSONANT, metathesis_strategy=MetathesisStrategy.H_CONS))
        ]

        if not TEST_CASES:
            self.skipTest("No test cases defined in TEST_CASES")

        deriver = StemDeriver()
        
        for case in TEST_CASES:
            definition = case[0]
            expected_pron = case[1]
            expected_pre = case[2] if len(case) > 2 else None

            with self.subTest(definition=definition):
                # Find the row in the corpus
                matching_rows = [r for r in self.corpus_rows if r.get('definition') == definition]
                self.assertTrue(matching_rows, f"No row found in corpus for definition: {definition}")
                
                found_match = False
                for row in matching_rows:
                    derivations = deriver.derive_row(row)
                    for d in derivations:
                        # 1. Full Derivation match
                        if isinstance(expected_pron, Derivation):
                            if d == expected_pron:
                                found_match = True
                                break
                            else:
                                continue

                        # 2. Config-based matching
                        # Check PronominalConfig
                        pron_match = True
                        if isinstance(expected_pron, PronominalConfig):
                            if d.pron_config != expected_pron:
                                pron_match = False
                        elif isinstance(expected_pron, dict):
                            for key, val in expected_pron.items():
                                if getattr(d.pron_config, key) != val:
                                    pron_match = False
                                    break
                        
                        # Check PrePronominalConfig if provided
                        pre_match = True
                        if expected_pre:
                            if isinstance(expected_pre, PrePronominalConfig):
                                if d.pre_config != expected_pre:
                                    pre_match = False
                            elif isinstance(expected_pre, dict):
                                for key, val in expected_pre.items():
                                    if getattr(d.pre_config, key) != val:
                                        pre_match = False
                                        break
                        
                        if pron_match and pre_match:
                            found_match = True
                            print(f"    [MATCH FOUND] Consensus Stem: '{d.consensus_stem}', Metathesis Involved: {d.metathesis_involved}")
                            break
                    if found_match:
                        break
                
                if not found_match:
                    if matching_rows:
                        self.diagnose_derivation(matching_rows[0], expected_pron, expected_pre)
                
                self.assertTrue(found_match, f"No derivation for '{definition}' matched expected configurations.")

if __name__ == '__main__':
    unittest.main()
