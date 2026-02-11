import unittest

from king_recreation.tone.analyze_tone_mvp import (
    check_prediction,
    generate_underlying_forms,
)


class TestToneIntegration(unittest.TestCase):
    def _test_integration(self, surface_form: str, underlying_expected: str):
        """
        Test that all generated underlying forms for a given surface form
        correctly infer the original surface form.
        """
        underlying_forms = generate_underlying_forms(surface_form)
        self.assertTrue(
            len(underlying_forms) > 0,
            f"No underlying forms generated for {surface_form}",
        )

        matched = False

        for u in underlying_forms:
            if u == underlying_expected:
                matched = True
            # print(f"Surface: {surface_form} -> Underlying: {u}")
            self.assertTrue(
                check_prediction(u, surface_form),
                f"Underlying form {u} fails to regenerate surface form {surface_form}",
            )

        self.assertTrue(
            matched,
            f"No underlying form {underlying_forms} matched {underlying_expected}",
        )

    def test_integration_2_32(self):
        self._test_integration("a2la32hs", "ala'hs")

    def test_integration_23_32(self):
        self._test_integration("i23nv32hs", "iinvv'hs")

    def test_integration_surface_glottal_post_c(self):
        self._test_integration("ga3'la", "gal'a")

    def test_integration_spreading_blocked_short(self):
        self._test_integration("nu33the22yo32l", "nuu'theeyo'l")

    def test_integration_spreading_blocked_long(self):
        self._test_integration("ga3'li22do33ha2", "gal'iidoo'ha")


if __name__ == "__main__":
    unittest.main()
