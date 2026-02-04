import unittest
import os
from king_recreation.phonology_data import MiddleVoice


class TestMiddleVoice(unittest.TestCase):
    def test_middle_ali(self):
        h_grade, g_grade = ("alhsday", "alihsday")
        expected = [
            (MiddleVoice.NONE, (h_grade, g_grade)),
            (MiddleVoice.AL_ALI, ("hsday", "hsday")),
        ]
        result = MiddleVoice.identify_middle_voice(h_grade, g_grade)

        self.assertTrue(
            repr(sorted(result, key=lambda x: x[0].value))
            == repr(sorted(expected, key=lambda x: x[0].value)),
            "Expected two possibilities",
        )

    def test_middle_ali_no_g(self):
        h_grade, g_grade = ("alhsday", None)
        expected = [
            (MiddleVoice.NONE, (h_grade, None)),
            (MiddleVoice.AL_ALI, ("hsday", None)),
        ]
        result = MiddleVoice.identify_middle_voice(h_grade, g_grade)

        self.assertTrue(
            repr(sorted(result, key=lambda x: x[0].value))
            == repr(sorted(expected, key=lambda x: x[0].value)),
            "Expected two possibilities",
        )

    def test_middle_atalen(self):
        h_grade, g_grade = ("atalen", None)
        expected = [
            (MiddleVoice.NONE, (h_grade, None)),
            (MiddleVoice.AT, ("alen", None)),
            (MiddleVoice.ATA, ("len", None)),
        ]
        result = MiddleVoice.identify_middle_voice(h_grade, g_grade)

        self.assertTrue(
            repr(sorted(result, key=lambda x: x[0].value))
            == repr(sorted(expected, key=lambda x: x[0].value)),
            "Expected two possibilities",
        )


if __name__ == "__main__":
    unittest.main()
