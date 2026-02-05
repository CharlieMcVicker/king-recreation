import os
import unittest

from king_recreation.derive_stems import StemDeriver
from king_recreation.phonology_data import get_pronominal_set_name
from king_recreation.reconstruct_from_roots import ReconstructionEngine


class TestHDroppingGeneralized(unittest.TestCase):
    def setUp(self):
        self.deriver = StemDeriver()
        # Mock class info not needed for derive_row usually, only for reconstruction
        # But ReconstructionEngine needs it.
        self.classes_path = "dummy_classes_h.csv"
        with open(self.classes_path, "w") as f:
            f.write("class,present,imperfective,perfective,imperative,infinitive\n")
            f.write("dummy,i,i,i,i,i\n")
        self.engine = ReconstructionEngine(self.classes_path)

    def tearDown(self):
        if os.path.exists(self.classes_path):
            os.remove(self.classes_path)

    def test_h_at_start(self):
        # Stem: hlogi
        # Present 3rd Set A (Non-dropping): gahlogi (ga- + hlogi)
        # Present 1sg Set A (Dropping): tsilogi (tsi- + logi)
        # Note: 'ga-' matches Consonant condition. 'h' is consonant.
        # 'tsi-' matches Consonant condition. 'l' is consonant.
        # Wait, if 'logi' is literal, does 'tsi-' match?
        # 'tsi-' is Condition.CONSONANT.
        # 'logi' starts with 'l' (consonant).
        # So 'tsi-' matches 'logi' naturally!
        # The trick is that 'hlogi' (target) must explain 'logi'.
        # drop_first_h('hlogi') -> 'logi'. 'logi' == 'logi'. Match!

        row = {"present": "kahlogi", "present_1sg": "tsilogi"}

        derivations = self.deriver.derive_row(row)

        found = False
        for d in derivations:
            if d.stems.get("present") == "hlogi":
                found = True
                break
        self.assertTrue(found, "Failed to derive 'hlogi' from 'gahlogi'/'tsilogi'")

    def test_h_after_vowel(self):
        # Stem: ahkwiyv
        # Present 3rd Set A (Non-dropping): ahkwiyv (prefix ø, Condition.VOWEL_AE)
        # Present 1sg Set A (Dropping): tsakwiyv (tsi- + akwiyv)
        # 'tsi-' is Condition.CONSONANT.
        # 'akwiyv' starts with 'a' (vowel).
        # Normally 'tsi-' shouldn't match.
        # But for h-dropping sets, we allow mismatch if underlying had h?
        # Wait, my code: `is_valid = remainder and (not self.is_vowel(remainder[0]) or is_h_drop)`
        # Yes, it allows vowel remainder for h-drop sets.
        # So 'tsi-' matches 'akwiyv'.
        # Literal: 'akwiyv'.
        # Target: 'ahkwiyv'.
        # drop_first_h('ahkwiyv') -> 'akwiyv'. Match!

        row = {"present": "ahkwiyv", "present_1sg": "tsakwiyv"}

        derivations = self.deriver.derive_row(row)

        found = False
        for d in derivations:
            if d.stems.get("present") == "ahkwiyv":
                found = True
                break
        self.assertTrue(found, "Failed to derive 'ahkwiyv' from 'ahkwiyv'/'tsakwiyv'")

    def test_reconstruction_h_drop(self):
        # Stem: ahkwiyv
        # Set: 1st Set A (h-dropping)
        # Expected: tsakwiyv (tsi- + akwiyv, where h is dropped)

        res = self.engine.generate_pronominal_forms("ahkwiyv", "1st Set A")
        self.assertIn("tsakwiyv", res)

    def test_reconstruction_h_start_drop(self):
        # Stem: hlogi
        # Set: 1st Set A
        # Expected: tsilogi (tsi- + logi)

        res = self.engine.generate_pronominal_forms("hlogi", "1st Set A")
        self.assertIn("tsilogi", res)


if __name__ == "__main__":
    unittest.main()
