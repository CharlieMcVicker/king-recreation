from dictionary_pipeline.tone.analyze_tone_mvp import (
    check_prediction,
    generate_underlying_forms,
)


def _test_integration(surface_form: str, underlying_expected: str):
    """
    Test that all generated underlying forms for a given surface form
    correctly infer the original surface form.
    """
    underlying_forms = generate_underlying_forms(surface_form)
    valid_underlying = [
        str(u) for u in underlying_forms if check_prediction(str(u), surface_form)
    ]

    assert (
        len(valid_underlying) > 0
    ), f"No valid underlying forms (that regenerate the surface) found for {surface_form}. Candidates were: {[str(u) for u in underlying_forms]}"

    assert (
        underlying_expected in valid_underlying
    ), f"Expected underlying form {underlying_expected} not found among valid candidates: {valid_underlying}"


def test_integration_2_32():
    _test_integration("a2la32hs", "ala'hs")


def test_integration_23_32():
    _test_integration("i23nv32hs", "iinvv'hs")


def test_integration_surface_glottal_post_c():
    _test_integration("ga3'la", "gal'a")


def test_integration_spreading_blocked_short():
    _test_integration("nu33the22yo32l", "nuu'theeyo'l")


def test_integration_spreading_blocked_long():
    _test_integration("ga3'li22do33ha2", "gal'iidoo'ha")
