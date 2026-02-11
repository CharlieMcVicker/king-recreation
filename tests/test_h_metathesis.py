import os

import pytest

from king_recreation.derive_stems import StemDeriver
from king_recreation.morphemes.prefixes.pronominals import get_pronominal_set_name
from king_recreation.reconstruct_from_roots import (
    ReconstructibleVerb,
    ReconstructionEngine,
)


@pytest.fixture
def metathesis_env():
    # Create a dummy classes file for the engine
    classes_path = "dummy_classes.csv"
    with open(classes_path, "w") as f:
        f.write("class,present,imperfective,perfective,imperative,infinitive\n")
        f.write("dummy,i,i,i,i,i\n")

    deriver = StemDeriver()
    engine = ReconstructionEngine(classes_path)

    yield deriver, engine, classes_path

    if os.path.exists(classes_path):
        os.remove(classes_path)


def test_derivation_singing(metathesis_env):
    deriver, engine, _ = metathesis_env
    # tekhanoki -> hnoki (3rd Set A + Distributive)
    # tuhnokis -> hnokis (3rd Set B + Distributive)
    row = {
        "present": "tekhanoki",
        "perfective": "tuhnokis",
        "definition": "singing",
    }
    derivations = deriver.derive_row(row)
    print(f"\nSinging Derivations: {[(d.set_type, d.stems) for d in derivations]}")
    assert any(
        "ahnoki" in d.stems.get("present", "").split(";") and d.set_type == "Set A"
        for d in derivations
    )


def test_reconstruction_singing(metathesis_env):
    _, engine, _ = metathesis_env
    # hnoki + ka- -> khanoki
    set_name = "3rd Set A"
    res = engine.generate_pronominal_forms("hnoki", set_name)
    assert "khanoki" in res


def test_reconstruction_tsha(metathesis_env):
    _, engine, _ = metathesis_env
    # hnaskwalo + tsa- -> tshanaskwalo (2nd Set B)
    set_name = "2nd Set B"
    res = engine.generate_pronominal_forms("hnaskwalo", set_name)
    assert "tshanaskwalo" in res


def test_derivation_mingling(metathesis_env):
    deriver, engine, _ = metathesis_env
    # khelatitoh -> ehlatitoh (3rd Set A)
    # perfective uhwelatitol helps disambiguate
    row = {
        "present": "khelatitoh",
        "perfective": "uhwelatitol",
        "definition": "mingling",
    }
    derivations = deriver.derive_row(row)
    print(f"Mingling A Derivations: {[(d.set_type, d.stems) for d in derivations]}")
    assert any(
        "ehlatitoh" in d.stems.get("present", "").split(";") and d.set_type == "Set A"
        for d in derivations
    )


def test_reconstruction_mingling_set_a(metathesis_env):
    _, engine, _ = metathesis_env
    # ehlatitoh + k- -> khelatitoh
    set_name = "3rd Set A"
    res = engine.generate_pronominal_forms("ehlatitoh", set_name)
    assert "khelatitoh" in res


def test_derivation_breathing(metathesis_env):
    deriver, engine, _ = metathesis_env
    # khawolate -> ahwolate (3rd Set A)
    # perfective uhwolates. If this results in 'ahwolate' due to METATHESIS_VOWEL, we check for that.
    row = {
        "present": "khawolate",
        "perfective": "uhwolates",
        "definition": "breathing",
    }
    derivations = deriver.derive_row(row)
    print(f"Breathing A Derivations: {[(d.set_type, d.stems) for d in derivations]}")
    assert any(
        "ahwolate" in d.stems.get("present", "").split(";") and d.set_type == "Set A"
        for d in derivations
    )


def test_reconstruction_breathing(metathesis_env):
    _, engine, _ = metathesis_env
    # ahwolate + k- -> khawolate
    set_name = "3rd Set A"
    res = engine.generate_pronominal_forms("ahwolate", set_name)
    assert "khawolate" in res


def test_derivation_mingling_set_b(metathesis_env):
    deriver, engine, _ = metathesis_env
    # uhwelatitoh -> ehlatitoh (3rd Set B)
    row = {
        "present": "uhwelatitoh",
        "perfective": "uhwelatitol",
        "definition": "mingling",
    }
    derivations = deriver.derive_row(row)
    print(f"Mingling B Derivations: {[(d.set_type, d.stems) for d in derivations]}")
    assert any(
        "ahwelatitoh" in d.stems.get("present", "").split(";") and d.set_type == "Set B"
        for d in derivations
    )


def test_reconstruction_mingling_set_b(metathesis_env):
    _, engine, _ = metathesis_env
    # ehlatitoh + uw- -> uhwelatitoh
    set_name = "3rd Set B"
    res = engine.generate_pronominal_forms("ehlatitoh", set_name)
    assert "uhwelatitoh" in res
