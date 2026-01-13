import unittest
import csv
import os
from king_recreation.derive_stems import StemDeriver, Derivation
from king_recreation.phonology_data import StemType, MetathesisStrategy, PronominalConfig, PrePronominalConfig

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
                            break
                    if found_match:
                        break
                
                self.assertTrue(found_match, f"No derivation for '{definition}' matched expected configurations.")

if __name__ == '__main__':
    unittest.main()
