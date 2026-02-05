import unittest

from king_recreation.derive_stems import StemDeriver, drop_first_h, is_strict_compatible


class TestHAlternationExtended(unittest.TestCase):
    def setUp(self):
        self.deriver = StemDeriver()

    def test_blinking_vowel_restoration(self):
        """
        Test 'he's closing his eyes' (blinking).
        Target (3rd): akhthastih (has h)
        Stem (1st): akathastih (h dropped, a restored)
        """
        target = "akhthastih"
        stem_1sg = "akathastih"

        # Current behavior:
        dropped = drop_first_h(target)  # akthastih
        self.assertEqual(dropped, "akthastih")

        # Strict check fails
        self.assertFalse(is_strict_compatible(stem_1sg, dropped))

        # We need a function that returns True for these
        # self.assertTrue(is_compatible_with_vowel_restoration(stem_1sg, dropped))

    def test_dancing_vowel_restoration(self):
        """
        Test 'he's dancing'.
        Target (3rd): alski (no explicit h, but acts syncopated)
        Stem (1st): aliski (vowel restored)
        """
        target = "alski"
        stem_1sg = "aliski"

        dropped = drop_first_h(target)  # alski (no h to drop)
        self.assertEqual(dropped, "alski")

        # Strict check fails
        self.assertFalse(is_strict_compatible(stem_1sg, dropped))

        # We need a function that returns True for these
        # self.assertTrue(is_compatible_with_vowel_restoration(stem_1sg, dropped))


if __name__ == "__main__":
    unittest.main()
