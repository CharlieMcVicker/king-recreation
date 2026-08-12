import csv
import os
import tempfile
from unittest.mock import patch

from dictionary_pipeline.dictionary_forms import (
    DictionaryVerb,
    Prediction,
    PredictionMeta,
)
from morphology.morphemes.prefixes import PrefixConfig
from morphology.morphemes.prefixes.prepronominals import PrePronominalConfig
from morphology.morphemes.prefixes.pronominals import PronominalConfig, StemType
from morphology.reconstruction import MorphologicalVerb
from morphology.word_spec import PronominalSet
from tex_dictionary.companion_data import load_mascot_map, select_deterministic_mascot
from tex_dictionary.mascot_resolver import MascotResolver


def test_aspect_class_mascots_csv_rw_compatibility():
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
        writer = csv.DictWriter(
            tmp, fieldnames=["class", "subclass", "variant", "mascot_corpus_id"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "class": "cause",
                "subclass": "",
                "variant": "Plain",
                "mascot_corpus_id": "61",
            }
        )
        writer.writerow(
            {
                "class": "stative",
                "subclass": "sub1",
                "variant": "Partitive",
                "mascot_corpus_id": "12",
            }
        )
        writer.writerow(
            {
                "class": "eventful",
                "subclass": "",
                "variant": "Plain",
                "mascot_corpus_id": "",
            }
        )
        tmp_path = tmp.name

    try:
        # Test loading via companion_data load_mascot_map
        with patch("tex_dictionary.companion_data.ASPECT_CLASS_MASCOTS_PATH", tmp_path):
            mascot_map = load_mascot_map()
            assert mascot_map.get("cause") == "61"
            assert mascot_map.get("stative-sub1") == "12"
            assert "eventful" not in mascot_map

        # Test loading via MascotResolver manual_mascots
        with patch(
            "tex_dictionary.mascot_resolver.ASPECT_CLASS_MASCOTS_PATH", tmp_path
        ):
            resolver = MascotResolver()
            assert resolver.manual_mascots.get(("cause", "Plain")) == 61
            assert resolver.manual_mascots.get(("stative-sub1", "Partitive")) == 12
            assert ("eventful", "Plain") not in resolver.manual_mascots
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_fallback_mascot_selection_omitted_or_unassigned():
    # Test select_deterministic_mascot in companion_data
    candidates = [
        {"present": "zebrastart"},
        {"present": "alphastart"},
        {"present": "betastart"},
    ]
    selected = select_deterministic_mascot(candidates)
    assert selected["present"] == "alphastart"

    # Test fallback resolution in MascotResolver when manual mascot is unassigned/omitted
    with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
        writer = csv.DictWriter(
            tmp, fieldnames=["class", "subclass", "variant", "mascot_corpus_id"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "class": "testclass",
                "subclass": "",
                "variant": "Plain",
                "mascot_corpus_id": "",
            }
        )
        tmp_path = tmp.name

    try:
        with patch(
            "tex_dictionary.mascot_resolver.ASPECT_CLASS_MASCOTS_PATH", tmp_path
        ):
            resolver = MascotResolver()

            # Mock matching verbs for testclass
            meta1 = PredictionMeta(
                corpus_id="100",
                definition="zebra verb",
                entry_no="1",
                prediction=Prediction.FULL_EVENTFUL,
            )
            morph1 = MorphologicalVerb(
                h_grade_root="verb1",
                glottal_grade_root=None,
                post_root_morpheme=None,
                class_name="testclass",
                config=PrefixConfig(
                    pre=PrePronominalConfig(),
                    pron=PronominalConfig(
                        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
                    ),
                ),
            )
            v1 = DictionaryVerb(meta=meta1, morphology=morph1)

            meta2 = PredictionMeta(
                corpus_id="200",
                definition="alpha verb",
                entry_no="2",
                prediction=Prediction.FULL_EVENTFUL,
            )
            morph2 = MorphologicalVerb(
                h_grade_root="verb2",
                glottal_grade_root=None,
                post_root_morpheme=None,
                class_name="testclass",
                config=PrefixConfig(
                    pre=PrePronominalConfig(),
                    pron=PronominalConfig(
                        set_type=PronominalSet.SET_A, stem_type=StemType.CONSONANT
                    ),
                ),
            )
            v2 = DictionaryVerb(meta=meta2, morphology=morph2)

            resolver.all_verbs = [v1, v2]

            with patch.object(resolver, "get_variant_label", return_value="Plain"):
                with patch("tex_dictionary.mascot_resolver.get_cnd_entry") as mock_cnd:

                    def side_effect(cid, form, corpus_to_cnd, cnd):
                        if cid == 100:
                            return {"no_tone": "zebra"}
                        return {"no_tone": "alpha"}

                    mock_cnd.side_effect = side_effect

                    resolved = resolver.resolve_mascot("testclass", "Plain")
                    assert resolved is not None
                    assert resolved.corpus_id == 200
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
