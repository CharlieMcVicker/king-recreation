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

        # test apply
        for voice, (h_stem, g_stem) in expected:
            h_stem = (
                voice.apply(h_stem, is_glottal_grade=False)
                if h_stem is not None
                else None
            )
            g_stem = (
                voice.apply(g_stem, is_glottal_grade=True)
                if g_stem is not None
                else None
            )

            self.assertEqual(
                (h_stem, g_stem),
                (h_grade, g_grade),
                f"Adding voice back in should recreate same forms (mv={voice})",
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

        # test apply
        for voice, (h_stem, g_stem) in expected:
            h_stem = (
                voice.apply(h_stem, is_glottal_grade=False)
                if h_stem is not None
                else None
            )
            g_stem = (
                voice.apply(g_stem, is_glottal_grade=True)
                if g_stem is not None
                else None
            )

            self.assertEqual(
                (h_stem, g_stem),
                (h_grade, g_grade),
                f"Adding voice back in should recreate same forms (mv={voice})",
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

        # test apply
        for voice, (h_stem, g_stem) in expected:
            h_stem = (
                voice.apply(h_stem, is_glottal_grade=False)
                if h_stem is not None
                else None
            )
            g_stem = (
                voice.apply(g_stem, is_glottal_grade=True)
                if g_stem is not None
                else None
            )

            self.assertEqual(
                (h_stem, g_stem),
                (h_grade, g_grade),
                f"Adding voice back in should recreate same forms (mv={voice})",
            )

    def test_try_stip(self):
        stems = {
            "present": "atawhahthvh",
            "present_1sg": "atawahthvh",
            "imperfective": "atawhahthvh",
            "perfective": "atawhahthvh",
            "imperative": "atawhahthvh",
            "infinitive": "atawhahthvh",
        }

        expected = {
            "present": "whahthvh",
            "present_1sg": "wahthvh",
            "imperfective": "whahthvh",
            "perfective": "whahthvh",
            "imperative": "whahthvh",
            "infinitive": "whahthvh",
        }

        voice = MiddleVoice.ATA

        res = {k: voice.try_strip_form(form) for k, form in stems.items()}

        self.assertEqual(res, expected, "Expected ata to be stripped")


if __name__ == "__main__":
    unittest.main()
