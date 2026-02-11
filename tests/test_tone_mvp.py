import unittest

from king_recreation.tone.analyze_tone_mvp import (
    Environment,
    GlottalPosition,
    H1Config,
    load_data,
    predict_h1_for_form,
)


class TestToneMVP(unittest.TestCase):
    def setUp(self):
        self.verbs, self.cnd_corpus, self.corpus_id_to_entries = load_data()

    def _test_case(self, test_str, expected, log=False):
        inferences = predict_h1_for_form(test_str)
        if log:
            for v, infs in inferences:
                print(f"Vowel: {v.quality} at {v.idx_start}")
                for inf in infs:
                    print(f"  {inf}")
        self.assertEqual(
            len(inferences),
            len(expected),
            f"Number of vowels with H1 mismatch for {test_str}. Got {len(inferences)}, expected {len(expected)}",
        )

        for i, ((v, inf), exp_list) in enumerate(zip(inferences, expected)):
            self.assertCountEqual(
                inf,
                exp_list,
                f"Possibilities mismatch for vowel {i} ({v.quality}) in {test_str}",
            )

    def test_2_32(self):
        self._test_case(
            test_str="a2la32hs",
            expected=[
                [
                    H1Config(
                        historically_long=False,
                        glottal_position=GlottalPosition.PRE_C,
                        env=Environment.NO_SPREAD,
                    ),
                ]
            ],
        )

    def test_23_32(self):
        self._test_case(
            test_str="i23nv32hs",
            expected=[
                [
                    H1Config(
                        historically_long=True,
                        glottal_position=GlottalPosition.PRE_C,
                        env=Environment.SPREAD,
                    ),
                    H1Config(
                        historically_long=False,
                        glottal_position=GlottalPosition.PRE_C,
                        env=Environment.SPREAD,
                    ),
                ]
            ],
        )

    def test_surface_glottal_post_c(self):
        self._test_case(
            test_str="ga3'la",
            expected=[
                [
                    H1Config(
                        historically_long=False,
                        glottal_position=GlottalPosition.POST_C,
                        env=Environment.NO_SPREAD,
                    ),
                ]
            ],
            log=True,
        )

    def test_spreading_blocked_short(self):
        self._test_case(
            test_str="nu33the22yo32l",
            expected=[
                [
                    H1Config(
                        historically_long=True,
                        glottal_position=GlottalPosition.POST_C,
                        env=Environment.NO_SPREAD,
                    ),
                    H1Config(
                        historically_long=True,
                        glottal_position=GlottalPosition.PRE_C,
                        env=Environment.NO_SPREAD,
                    ),
                ],
                [
                    H1Config(
                        historically_long=False,
                        glottal_position=GlottalPosition.PRE_C,
                        env=Environment.NO_SPREAD,
                    ),
                ],
            ],
            log=True,
        )

    def test_spreading_blocked_long(self):
        self._test_case(
            test_str="ga3'li22do33ha2",
            expected=[
                [
                    H1Config(
                        historically_long=False,
                        glottal_position=GlottalPosition.POST_C,
                        env=Environment.NO_SPREAD,
                    ),
                ],
                [
                    H1Config(
                        historically_long=True,
                        glottal_position=GlottalPosition.PRE_C,
                        env=Environment.NO_SPREAD,
                    ),
                    H1Config(
                        historically_long=True,
                        glottal_position=GlottalPosition.POST_C,
                        env=Environment.NO_SPREAD,
                    ),
                ],
            ],
            log=True,
        )

    def test_h2_short_next(self):
        # a/ followed by short la -> a3la
        # next is short, so H2 becomes 3 and does NOT block H1 on following syllables.
        from king_recreation.tone.analyze_tone_mvp import LexedForm, check_prediction

        self.assertTrue(check_prediction("a/la", "a3la"))
        self.assertFalse(check_prediction("a/la", "a33la"))

    def test_h2_long_next(self):
        # a/ followed by long laa -> a33laa
        # next is long, so H2 becomes 33 and DOES block H1 on following syllables.
        from king_recreation.tone.analyze_tone_mvp import (
            LexedForm,
            check_prediction,
            infer_surface_forms,
        )

        self.assertTrue(check_prediction("a/laa'", "a33la2'"))

    def test_h2_parsing(self):
        from king_recreation.tone.analyze_tone_mvp import LexedForm

        lf = LexedForm.from_str("ga/li")
        # tokens: [Consonant(g), HistoricalVowel(a, h2=True), Consonant(l), HistoricalVowel(i)]
        self.assertTrue(lf.tokens[1].h2)
        self.assertEqual(str(lf), "ga/li")

    def test_h2_brute_force_generation(self):
        # Test that generate_underlying_forms finds H2
        from king_recreation.tone.analyze_tone_mvp import generate_underlying_forms

        candidates = generate_underlying_forms("a3-la3")
        underlying_strs = [str(c) for c in candidates]
        self.assertIn("a/-la", underlying_strs)

        candidates_long = generate_underlying_forms("a23-la33")
        underlying_strs_long = [str(c) for c in candidates_long]
        # aa/ because surface is 33 (long)
        self.assertIn("aa/-laa", underlying_strs_long)

    def test_h2_23_33(self):
        from king_recreation.tone.analyze_tone_mvp import generate_underlying_forms

        candidates = generate_underlying_forms("ka2ne23tl-i33y-v2'-a")
        underlying_strs = [str(c) for c in candidates]
        self.assertIn("kanee/tl-iiy-vv'-a", underlying_strs)


if __name__ == "__main__":
    unittest.main()
