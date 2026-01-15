import unittest
from collections import defaultdict
from king_recreation.class_patterns import ClassPatterns
from king_recreation.classify_verbs import get_matches_for_verb


class TestPatternOptimization(unittest.TestCase):

    def setUp(self):
        # Create mock patterns
        # Group "test_macro":
        # 1. Base: pres=a, imp=b
        # 2. Var1: pres=a, imp=c
        # 3. Var2: pres=a (unspecified imp)

        self.p_base = ClassPatterns(
            name="test_macro",
            stem_finals=[""],
            present="a",
            imperfective="",
            perfective="",
            imperative="b",
            infinitive="",
            _original_data={"class": "test_macro"},
        )
        self.p_var1 = ClassPatterns(
            name="test_macro[imp2]",
            stem_finals=[""],
            present="a",
            imperfective="",
            perfective="",
            imperative="c",
            infinitive="",
            _original_data={"class": "test_macro"},
        )
        self.p_gen = ClassPatterns(
            name="test_macro[gen]",
            stem_finals=[""],
            present="a",
            imperfective="",
            perfective="",
            imperative="",
            infinitive="",
            _original_data={"class": "test_macro"},
        )

        self.macro_groups = defaultdict(list)
        self.macro_groups["test_macro"] = [self.p_base, self.p_var1, self.p_gen]

    def test_pruning_missing_form(self):
        # Verb: pres=a (missing imp)
        # Signatures based on present only: (a,)
        # All 3 patterns have pres=a.
        # They fall in same bucket.
        # Specificity: Base(2), Var1(2), Gen(1).
        # Min specificity -> Gen.
        # Candidates -> [Gen].
        # Gen matches "a".
        # Result: Should match Gen only.

        verb = {"present": "a"}  # missing imperative
        matches = get_matches_for_verb(verb, self.macro_groups)

        self.assertEqual(len(matches), 2)  # Strict and Loose for the ONE match
        # Verify it matched Gen
        self.assertEqual(matches[0]["class"], "test_macro[gen]")

    def test_specificity_priority(self):
        # Verb: pres=a, imp=b
        # Signatures based on pres, imp:
        # Base: (a, b)
        # Var1: (a, c)
        # Gen: (a, "")
        # All different buckets?
        # Yes.
        # Candidates: [Base, Var1, Gen]
        # Specificity: Base(2), Var1(2), Gen(1).
        # Sort: [Base, Var1, Gen] (assuming B before V).
        # Check Base: Matches (a, b) == (a, b). Match! -> Stop.
        # Result: Base.

        verb = {"present": "a", "imperative": "b"}
        matches = get_matches_for_verb(verb, self.macro_groups)

        # We now expect MULTIPLE matches because we removed the "stop after first match" logic.
        # Base (pres=a, imp=b) matches.
        # Gen (pres=a, imp="") matches (vacuously).
        # We just want to ensure we didn't lose the matches.

        match_names = [m["class"] for m in matches]
        self.assertIn("test_macro", match_names)
        self.assertIn("test_macro[gen]", match_names)

    def test_mismatch_retry(self):
        # Verb: pres=a, imp=c
        # Signatures: Base(a, b), Var1(a, c), Gen(a, "")
        # Candidates: [Base, Var1, Gen]
        # Sort: [Base, Var1, Gen]
        # Check Base: Fail (imp b!=c)
        # Check Var1: Match (imp c==c) -> Stop.
        # Result: Var1.

        verb = {"present": "a", "imperative": "c"}
        matches = get_matches_for_verb(verb, self.macro_groups)

        self.assertEqual(matches[0]["class"], "test_macro[imp2]")

    def test_vacuous_match_with_specificity(self):
        # Verb: pres=a, imp=d (unknown to patterns)
        # Base: imp=b -> Fail
        # Var1: imp=c -> Fail
        # Gen: imp="" -> Matches?
        # match_ending(d, "", strict) -> ends_with("") -> True.
        # So Gen should match.

        verb = {"present": "a", "imperative": "d"}
        matches = get_matches_for_verb(verb, self.macro_groups)

        self.assertEqual(matches[0]["class"], "test_macro[gen]")


if __name__ == "__main__":
    unittest.main()
