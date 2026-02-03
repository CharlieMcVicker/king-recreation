import unittest
from king_recreation.pattern_registry import PatternRegistry


class TestPreconditions(unittest.TestCase):
    def setUp(self):
        self.registry = PatternRegistry.get_instance()
        self.registry.load_from_csv("data/classes.csv")

    def test_o_macro_preconditions(self):
        # 'o' class has 'C' precondition
        candidates = self.registry.get_candidates("ko'", "present")
        o_candidates = [c for c in candidates if c.name.startswith("o")]
        self.assertTrue(
            len(o_candidates) > 0,
            "Should match 'o' class when preceded by consonant 'k'",
        )

        candidates = self.registry.get_candidates("ao'", "present")
        o_candidates = [c for c in candidates if c.name.startswith("o")]
        self.assertEqual(
            len(o_candidates),
            0,
            "Should NOT match 'o' class when preceded by vowel 'a'",
        )

    def test_sequence_precondition_hV(self):
        # 'hvsk-n' class has 'hV' precondition
        # hvsk,n,hV,hvhsk,hvhsk,n,hvka,*oht

        # 'oht' is the suffix for infinitive (bypassed if it has *, but let's check 'n' for base)
        # Wait, 'hvsk-n' row has 'n' for perfective? No, 'n' for imperative.

        # Row 13 (from user diff): hvsk,n,hV,hvhsk,hvhsk,n,hvka,*oht
        # Fields: class, subclass, preconditions, present, imperfective, perfective, imperative, infinitive
        # present: hvhsk, imperfective: hvhsk, perfective: n, imperative: hvka, infinitive: *oht

        # Test perfective 'n':
        # Case 1: Preceded by 'ha' (h + V) -> Should Match
        candidates = self.registry.get_candidates("han", "perfective")
        n_candidates = [c for c in candidates if c.name.startswith("hvsk-n")]
        self.assertTrue(
            len(n_candidates) > 0,
            "Should match 'hvsk-n' perfective 'n' when preceded by 'ha' (hV)",
        )

        # Case 2: Preceded by 'ka' (k + V) -> Should NOT Match
        candidates = self.registry.get_candidates("kan", "perfective")
        n_candidates = [c for c in candidates if c.name.startswith("hvsk-n")]
        self.assertEqual(
            len(n_candidates),
            0,
            "Should NOT match 'hvsk-n' when preceded by 'ka' (not hV)",
        )

        # Case 3: Preceded by 'h' but no V (hn) -> Should NOT Match
        candidates = self.registry.get_candidates("hnn", "perfective")
        n_candidates = [c for c in candidates if c.name.startswith("hvsk-n")]
        self.assertEqual(
            len(n_candidates),
            0,
            "Should NOT match 'hvsk-n' when preceded by 'hn' (not hV)",
        )

        # Case 4: Preceded by 'a' but no h (an) -> Should NOT Match
        candidates = self.registry.get_candidates(
            "an", "perfective"
        )  # suffix 'n', preceding 'a'
        n_candidates = [c for c in candidates if c.name.startswith("hvsk-n")]
        self.assertEqual(
            len(n_candidates),
            0,
            "Should NOT match 'hvsk-n' when preceded by 'a' (not hV)",
        )


if __name__ == "__main__":
    unittest.main()
