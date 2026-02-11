import os

import pytest

from king_recreation.derive_stems import StemDeriver
from king_recreation.morphemes.prefixes.pronominals import get_pronominal_set_name
from king_recreation.reconstruct_from_roots import ReconstructionEngine


@pytest.fixture
def h_dropping_env():
    classes_path = "dummy_classes_h.csv"
    with open(classes_path, "w") as f:
        f.write("class,present,imperfective,perfective,imperative,infinitive\n")
        f.write("dummy,i,i,i,i,i\n")

    deriver = StemDeriver()
    engine = ReconstructionEngine(classes_path)

    yield deriver, engine, classes_path

    if os.path.exists(classes_path):
        os.remove(classes_path)


def test_h_at_start(h_dropping_env):
    deriver, engine, _ = h_dropping_env
    row = {"present": "kahlogi", "present_1sg": "tsilogi"}
    derivations = deriver.derive_row(row)

    found = False
    for d in derivations:
        if d.stems.get("present") == "hlogi":
            found = True
            break
    assert found, "Failed to derive 'hlogi' from 'gahlogi'/'tsilogi'"


def test_h_after_vowel(h_dropping_env):
    deriver, engine, _ = h_dropping_env
    row = {"present": "ahkwiyv", "present_1sg": "tsakwiyv"}
    derivations = deriver.derive_row(row)

    found = False
    for d in derivations:
        if d.stems.get("present") == "ahkwiyv":
            found = True
            break
    assert found, "Failed to derive 'ahkwiyv' from 'ahkwiyv'/'tsakwiyv'"


def test_reconstruction_h_drop(h_dropping_env):
    deriver, engine, _ = h_dropping_env
    res = engine.generate_pronominal_forms("ahkwiyv", "1st Set A")
    assert "tsakwiyv" in res


def test_reconstruction_h_start_drop(h_dropping_env):
    deriver, engine, _ = h_dropping_env
    res = engine.generate_pronominal_forms("hlogi", "1st Set A")
    assert "tsilogi" in res
