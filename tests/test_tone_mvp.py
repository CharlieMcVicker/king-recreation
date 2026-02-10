import unittest

from king_recreation.tone.analyze_tone_mvp import load_data


class TestToneMVP(unittest.TestCase):
    def setUp(self):
        self.verbs, self.cnd_corpus, self.corpus_id_to_entries = load_data()

    def test_no_h1_no_h2(self):
        pass


if __name__ == "__main__":
    unittest.main()
