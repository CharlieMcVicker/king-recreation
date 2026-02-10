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
                for inf in infs:
                    print(v, inf)
        self.assertEqual(len(inferences), 1)
        ((v, inf),) = inferences
        self.assertEqual(len(inf), len(expected))

        for exp in expected:
            self.assertTrue(exp in inf, str(inf))

    def test_2_32(self):
        self._test_case(
            test_str="a2la32hs",
            expected=[
                H1Config(
                    historically_long=False,
                    glottal_position=GlottalPosition.PRE_C,
                    env=Environment.NO_SPREAD,
                ),
            ],
        )

    def test_23_32(self):
        self._test_case(
            test_str="i23nv32hs",
            expected=[
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
            ],
        )

    def test_surface_glottal_post_c(self):
        self._test_case(
            test_str="ga3'la",
            expected=[
                H1Config(
                    historically_long=False,
                    glottal_position=GlottalPosition.POST_C,
                    env=Environment.NO_SPREAD,
                ),
            ],
            log=True,
        )


if __name__ == "__main__":
    unittest.main()
