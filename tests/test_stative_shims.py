"""Tests for stative_shims load/save logic.

Covers:
  - load_stative_shims() with new multi-row format (user_selected column present)
  - load_stative_shims() with legacy format (no user_selected column) — backward compat
  - save_stative_shims() writes all candidates, marks pipeline_selected and user_selected
  - save_stative_shims() bails on unmatched curated override (exit 1)
"""

import csv
import os
from pathlib import Path

import pytest

from dictionary_pipeline.dictionary_forms import (
    DictionaryVerb,
    Prediction,
    PredictionMeta,
)
from dictionary_pipeline.phases.select_canonical_derivations import (
    load_stative_shims,
    save_stative_shims,
    validate_shim_compatibility,
)
from morphology.morphemes.prefixes import PrefixConfig
from morphology.reconstruction import MorphologicalVerb

# ---------------------------------------------------------------------------
# Helpers / Fakes
# ---------------------------------------------------------------------------


def _make_verb(
    corpus_id: str,
    prediction: str,
    h_grade: str,
    cls: str = "go-in",
    stem_type: str = "vowel_a",
    middle_voice: str = "atat",
    plural: str = "False",
    g_grade: str | None = None,
    original_data: dict[str, str] | None = None,
) -> DictionaryVerb:
    """Create a minimal DictionaryVerb for testing."""
    data: dict[str, str] = original_data or {
        "corpus_id": corpus_id,
        "prediction": prediction,
        "class": cls,
        "h_grade": h_grade,
        "g_grade": g_grade or "",
        "post_root_morpheme": "",
        "set_a_b": "a",
        "stem_type": stem_type,
        "allow_h_metathesis": "False",
        "middle_voice": middle_voice,
        "middle_voice_h_metathesis": "False",
        "plural": plural,
        "ka_variant": "False",
        "aki_1st": "False",
        "uwa_v": "False",
        "3rd_person_object": "False",
        "translocutive": "False",
        "translocutive_imp_only": "False",
        "partitive": "False",
        "distributive": "False",
        "metathesis_involved": "False",
        "segmented_forms": "",
        "entry_no": "1",
        "definition": "to go",
        "user_selected": "",
        "pipeline_selected": "",
    }

    meta = PredictionMeta(
        corpus_id=corpus_id,
        definition=data.get("definition", "to go"),
        entry_no=data.get("entry_no", "1"),
        prediction=Prediction(prediction),
    )
    config = PrefixConfig.from_row(data)
    morphology = MorphologicalVerb(
        h_grade_root=h_grade,
        glottal_grade_root=g_grade if g_grade else None,
        post_root_morpheme=None,
        class_name=cls,
        config=config,
    )
    return DictionaryVerb(meta=meta, morphology=morphology, original_data=data)


def _write_csv(path: str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Tests for load_stative_shims()
# ---------------------------------------------------------------------------


class TestLoadStativeShims:
    def test_returns_empty_when_file_missing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("STATIVE_SHIMS_PATH", str(tmp_path / "stative_shims.csv"))

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(tmp_path / "stative_shims.csv")

        result = load_stative_shims()
        paths.STATIVE_SHIMS_PATH = original
        assert result == {}

    def test_new_format_returns_only_user_selected(self, tmp_path: Path) -> None:
        """Multi-row format: only rows with user_selected='x' are returned as overrides."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"
        fieldnames = [
            "corpus_id",
            "entry_no",
            "definition",
            "prediction",
            "user_selected",
            "pipeline_selected",
            "class",
            "post_root_morpheme",
            "h_grade",
            "g_grade",
            "translocutive",
            "translocutive_imp_only",
            "partitive",
            "distributive",
            "set_a_b",
            "stem_type",
            "allow_h_metathesis",
            "middle_voice",
            "middle_voice_h_metathesis",
            "plural",
            "ka_variant",
            "aki_1st",
            "uwa_v",
            "3rd_person_object",
            "metathesis_involved",
            "segmented_forms",
        ]
        rows = [
            # Two candidates for corpus_id 42 — only second is user-selected
            {fn: "" for fn in fieldnames}
            | {
                "corpus_id": "42",
                "h_grade": "atat",
                "user_selected": "",
                "pipeline_selected": "x",
                "stem_type": "vowel_a",
            },
            {fn: "" for fn in fieldnames}
            | {
                "corpus_id": "42",
                "h_grade": "atat",
                "user_selected": "x",
                "pipeline_selected": "",
                "stem_type": "s_stem",
            },
            # corpus_id 99 — no user selection
            {fn: "" for fn in fieldnames}
            | {
                "corpus_id": "99",
                "h_grade": "nv",
                "user_selected": "",
                "pipeline_selected": "x",
                "stem_type": "con",
            },
        ]
        _write_csv(str(shims_path), fieldnames, rows)

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        result = load_stative_shims()

        paths.STATIVE_SHIMS_PATH = original

        assert set(result.keys()) == {"42"}
        assert result["42"]["stem_type"] == "s_stem"
        assert result["42"]["user_selected"] == "x"

    def test_legacy_format_treats_all_rows_as_overrides(self, tmp_path: Path) -> None:
        """Legacy format (no user_selected column): every row is treated as an override."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"
        legacy_fieldnames = [
            "corpus_id",
            "prediction",
            "class",
            "h_grade",
            "g_grade",
            "post_root_morpheme",
            "set_a_b",
            "stem_type",
            "allow_h_metathesis",
            "middle_voice",
            "middle_voice_h_metathesis",
            "plural",
            "ka_variant",
            "aki_1st",
            "uwa_v",
            "3rd_person_object",
            "translocutive",
            "translocutive_imp_only",
            "partitive",
            "distributive",
        ]
        rows = [
            {fn: "" for fn in legacy_fieldnames}
            | {"corpus_id": "10", "h_grade": "gv", "stem_type": "vowel_a"},
            {fn: "" for fn in legacy_fieldnames}
            | {"corpus_id": "20", "h_grade": "di", "stem_type": "con"},
        ]
        _write_csv(str(shims_path), legacy_fieldnames, rows)

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        result = load_stative_shims()

        paths.STATIVE_SHIMS_PATH = original

        assert set(result.keys()) == {"10", "20"}
        assert result["10"]["stem_type"] == "vowel_a"
        assert result["20"]["stem_type"] == "con"


# ---------------------------------------------------------------------------
# Tests for save_stative_shims()
# ---------------------------------------------------------------------------


class TestSaveStativeShims:
    def test_writes_all_candidates_for_stative_ids(self, tmp_path: Path) -> None:
        """save_stative_shims writes one row per INF_EVENTFUL candidate."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"

        # Verb 10 is FULL_STATIVE; verbs 11, 12 are INF_EVENTFUL sharing root "atat"
        stative = _make_verb("10", "FullStative", "atat")
        cand_a = _make_verb("10", "InfEventful", "atat", stem_type="vowel_a")
        cand_b = _make_verb("10", "InfEventful", "atat", stem_type="s_stem")

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        save_stative_shims(
            validated_verbs=[stative, cand_a, cand_b],
            stative_corpus_ids={"10"},
            curated_overrides={},
        )

        paths.STATIVE_SHIMS_PATH = original

        assert shims_path.exists()
        with open(shims_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        assert len(rows) == 2

    def test_marks_pipeline_selected_on_first_sorted_candidate(
        self, tmp_path: Path
    ) -> None:
        """save_stative_shims marks pipeline_selected='x' on the sort_candidates winner."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"

        stative = _make_verb("10", "FullStative", "atat")
        # con stem_type has priority 0 in sort_candidates
        cand_con = _make_verb("10", "InfEventful", "atat", stem_type="con")
        cand_vowel = _make_verb("10", "InfEventful", "atat", stem_type="vowel_a")

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        save_stative_shims(
            validated_verbs=[stative, cand_con, cand_vowel],
            stative_corpus_ids={"10"},
            curated_overrides={},
        )

        paths.STATIVE_SHIMS_PATH = original

        with open(shims_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        pipeline_rows = [r for r in rows if r["pipeline_selected"] == "x"]
        assert len(pipeline_rows) == 1
        assert pipeline_rows[0]["stem_type"] == "con"

    def test_marks_user_selected_when_override_matches(self, tmp_path: Path) -> None:
        """save_stative_shims marks user_selected='x' when a curated override matches."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"

        stative = _make_verb("10", "FullStative", "atat")
        cand_a = _make_verb("10", "InfEventful", "atat", stem_type="vowel_a")
        cand_b = _make_verb("10", "InfEventful", "atat", stem_type="s_stem")

        # curated_overrides says user wants s_stem
        curated_overrides = {
            "10": {
                "stem_type": "s_stem",
                "allow_h_metathesis": "False",
                "middle_voice_h_metathesis": "False",
                "plural": "False",
                "ka_variant": "False",
                "aki_1st": "False",
                "uwa_v": "False",
                "3rd_person_object": "False",
                "translocutive": "False",
                "translocutive_imp_only": "False",
                "partitive": "False",
                "distributive": "False",
            }
        }

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        save_stative_shims(
            validated_verbs=[stative, cand_a, cand_b],
            stative_corpus_ids={"10"},
            curated_overrides=curated_overrides,
        )

        paths.STATIVE_SHIMS_PATH = original

        with open(shims_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        user_rows = [r for r in rows if r["user_selected"] == "x"]
        assert len(user_rows) == 1
        assert user_rows[0]["stem_type"] == "s_stem"

    def test_bails_when_override_not_matched(self, tmp_path: Path) -> None:
        """save_stative_shims calls exit(1) when a curated override cannot be matched."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"

        stative = _make_verb("10", "FullStative", "atat")
        cand_a = _make_verb("10", "InfEventful", "atat", stem_type="vowel_a")

        # Override specifies a stem_type that doesn't exist
        curated_overrides = {"10": {"stem_type": "nonexistent_stem_type"}}

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        with pytest.raises(SystemExit) as exc_info:
            save_stative_shims(
                validated_verbs=[stative, cand_a],
                stative_corpus_ids={"10"},
                curated_overrides=curated_overrides,
            )

        paths.STATIVE_SHIMS_PATH = original

        assert exc_info.value.code == 1
        # File should NOT have been written (save was aborted)
        assert not shims_path.exists()

    def test_writes_no_file_when_no_candidates(self, tmp_path: Path) -> None:
        """save_stative_shims is a no-op when no INF_EVENTFUL candidates exist."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"

        stative = _make_verb("10", "FullStative", "atat")

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        save_stative_shims(
            validated_verbs=[stative],
            stative_corpus_ids={"10"},
            curated_overrides={},
        )

        paths.STATIVE_SHIMS_PATH = original

        assert not shims_path.exists()


# ---------------------------------------------------------------------------
# Tests for validate_shim_compatibility()  (TASK-4.4)
# ---------------------------------------------------------------------------


class TestValidateShimCompatibility:
    """Unit tests for validate_shim_compatibility().

    Rules under test:
      - glottal_grade_root: must match unless either side is None.
      - middle_voice: must match.
      - plural_pronouns: must match.
      - class_name, post_root_morpheme, set_type: NOT checked.
    """

    def test_identical_config_is_compatible(self) -> None:
        """Two verbs with the same middle_voice and plural are compatible."""
        base = _make_verb(
            "1", "FullStative", "atat", middle_voice="atat", plural="False"
        )
        shim = _make_verb(
            "1", "InfEventful", "atat", middle_voice="atat", plural="False"
        )
        ok, mismatches = validate_shim_compatibility(base, shim)
        assert ok is True
        assert mismatches == []

    def test_incompatible_middle_voice(self) -> None:
        """Differing middle_voice makes the shim incompatible."""
        base = _make_verb("1", "FullStative", "atat", middle_voice="atat")
        shim = _make_verb("1", "InfEventful", "atat", middle_voice="none")
        ok, mismatches = validate_shim_compatibility(base, shim)
        assert ok is False
        assert any("middle_voice" in m for m in mismatches)

    def test_incompatible_plural(self) -> None:
        """Differing plural_pronouns makes the shim incompatible."""
        base = _make_verb("1", "FullStative", "atat", plural="False")
        shim = _make_verb("1", "InfEventful", "atat", plural="True")
        ok, mismatches = validate_shim_compatibility(base, shim)
        assert ok is False
        assert any("plural_pronouns" in m for m in mismatches)

    def test_g_grade_null_on_base_is_compatible(self) -> None:
        """None g_grade on the base verb does not block compatibility."""
        base = _make_verb("1", "FullStative", "atat", g_grade=None)
        shim = _make_verb("1", "InfEventful", "atat", g_grade="atat")
        ok, mismatches = validate_shim_compatibility(base, shim)
        assert ok is True
        assert mismatches == []

    def test_g_grade_null_on_shim_is_compatible(self) -> None:
        """None g_grade on the shim does not block compatibility."""
        base = _make_verb("1", "FullStative", "atat", g_grade="atat")
        shim = _make_verb("1", "InfEventful", "atat", g_grade=None)
        ok, mismatches = validate_shim_compatibility(base, shim)
        assert ok is True
        assert mismatches == []

    def test_g_grade_mismatch_both_non_null_is_incompatible(self) -> None:
        """When both g_grades are non-None but differ, the shim is incompatible."""
        base = _make_verb("1", "FullStative", "atat", g_grade="atat")
        shim = _make_verb("1", "InfEventful", "atat", g_grade="other")
        ok, mismatches = validate_shim_compatibility(base, shim)
        assert ok is False
        assert any("glottal_grade_root" in m for m in mismatches)

    def test_different_class_is_compatible(self) -> None:
        """suffix class (class_name) is NOT a matching criterion."""
        base = _make_verb("1", "FullStative", "atat", cls="go-in")
        shim = _make_verb("1", "InfEventful", "atat", cls="entirely-different-class")
        ok, mismatches = validate_shim_compatibility(base, shim)
        assert ok is True
        assert mismatches == []

    def test_different_set_type_is_compatible(self) -> None:
        """set_a_b is NOT a matching criterion."""
        base_data = {
            "corpus_id": "1",
            "prediction": "FullStative",
            "class": "go-in",
            "h_grade": "atat",
            "g_grade": "",
            "post_root_morpheme": "",
            "set_a_b": "b",
            "stem_type": "vowel_a",
            "allow_h_metathesis": "False",
            "middle_voice": "atat",
            "middle_voice_h_metathesis": "False",
            "plural": "False",
            "ka_variant": "False",
            "aki_1st": "False",
            "uwa_v": "False",
            "3rd_person_object": "False",
            "translocutive": "False",
            "translocutive_imp_only": "False",
            "partitive": "False",
            "distributive": "False",
            "metathesis_involved": "False",
            "segmented_forms": "",
            "entry_no": "1",
            "definition": "to go",
            "user_selected": "",
            "pipeline_selected": "",
        }
        shim_data = {**base_data, "prediction": "InfEventful", "set_a_b": "a"}
        base = _make_verb("1", "FullStative", "atat", original_data=base_data)
        shim = _make_verb("1", "InfEventful", "atat", original_data=shim_data)
        ok, mismatches = validate_shim_compatibility(base, shim)
        assert ok is True
        assert mismatches == []

    def test_mismatch_details_are_informative(self) -> None:
        """Mismatch strings include field names for easy debugging."""
        base = _make_verb(
            "1", "FullStative", "atat", middle_voice="atat", plural="True"
        )
        shim = _make_verb(
            "1", "InfEventful", "atat", middle_voice="none", plural="False"
        )
        ok, mismatches = validate_shim_compatibility(base, shim)
        assert ok is False
        assert len(mismatches) == 2
        assert any("middle_voice" in m for m in mismatches)
        assert any("plural_pronouns" in m for m in mismatches)


# ---------------------------------------------------------------------------
# Integration tests: compatibility filtering inside the pipeline
# ---------------------------------------------------------------------------


class TestShimCompatibilityInPipeline:
    """Tests that validate_shim_compatibility is enforced during shim selection
    and save_stative_shims()."""

    def test_incompatible_candidates_excluded_from_csv(self, tmp_path: Path) -> None:
        """Candidates that fail compatibility are not written to the CSV."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"

        # base stative has middle_voice=atat, plural=False
        stative = _make_verb(
            "10", "FullStative", "atat", middle_voice="atat", plural="False"
        )
        # compatible shim: same middle_voice + plural
        cand_ok = _make_verb(
            "10",
            "InfEventful",
            "atat",
            middle_voice="atat",
            plural="False",
            stem_type="con",
        )
        # incompatible shim: different middle_voice
        cand_bad = _make_verb(
            "10",
            "InfEventful",
            "atat",
            middle_voice="none",
            plural="False",
            stem_type="vowel_a",
        )

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        save_stative_shims(
            validated_verbs=[stative, cand_ok, cand_bad],
            stative_corpus_ids={"10"},
            curated_overrides={},
        )

        paths.STATIVE_SHIMS_PATH = original

        assert shims_path.exists()
        with open(shims_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        # Only the compatible candidate should appear
        assert len(rows) == 1
        assert rows[0]["stem_type"] == "con"

    def test_user_selected_incompatible_shim_causes_exit1_in_save(
        self, tmp_path: Path
    ) -> None:
        """save_stative_shims exits with code 1 when the user-selected shim
        fails compatibility (e.g. after the base verb's middle_voice changed)."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"

        # Base verb has middle_voice=atat
        stative = _make_verb("10", "FullStative", "atat", middle_voice="atat")
        # The only candidate has middle_voice=none — incompatible with base
        cand = _make_verb(
            "10", "InfEventful", "atat", middle_voice="none", stem_type="con"
        )

        # Pretend the user previously selected this (now incompatible) candidate
        curated_overrides = {
            "10": {
                "stem_type": "con",
                "middle_voice": "none",
                "allow_h_metathesis": "False",
                "middle_voice_h_metathesis": "False",
                "plural": "False",
                "ka_variant": "False",
                "aki_1st": "False",
                "uwa_v": "False",
                "3rd_person_object": "False",
                "translocutive": "False",
                "translocutive_imp_only": "False",
                "partitive": "False",
                "distributive": "False",
            }
        }

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        with pytest.raises(SystemExit) as exc_info:
            save_stative_shims(
                validated_verbs=[stative, cand],
                stative_corpus_ids={"10"},
                curated_overrides=curated_overrides,
            )

        paths.STATIVE_SHIMS_PATH = original

        assert exc_info.value.code == 1
        assert not shims_path.exists()

    def test_compatible_shim_is_bound_in_selection_loop(self, tmp_path: Path) -> None:
        """Only compatible candidates are pipeline-selected in save_stative_shims."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"

        stative = _make_verb(
            "10", "FullStative", "atat", middle_voice="atat", plural="False"
        )
        # Two shims: one compatible (con), one not (different middle_voice)
        cand_compatible = _make_verb(
            "10",
            "InfEventful",
            "atat",
            middle_voice="atat",
            plural="False",
            stem_type="con",
        )
        cand_incompatible = _make_verb(
            "10",
            "InfEventful",
            "atat",
            middle_voice="none",
            plural="False",
            stem_type="vowel_a",
        )

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        save_stative_shims(
            validated_verbs=[stative, cand_compatible, cand_incompatible],
            stative_corpus_ids={"10"},
            curated_overrides={},
        )

        paths.STATIVE_SHIMS_PATH = original

        with open(shims_path, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))

        pipeline_rows = [r for r in rows if r["pipeline_selected"] == "x"]
        assert len(pipeline_rows) == 1
        assert pipeline_rows[0]["stem_type"] == "con"

    def test_no_shim_bound_when_all_candidates_incompatible(
        self, tmp_path: Path
    ) -> None:
        """When all InfEventful candidates fail compatibility, CSV is empty and
        no shim is bound to the canonical verb."""
        shims_path = tmp_path / "curated" / "stative_shims.csv"

        stative = _make_verb("10", "FullStative", "atat", middle_voice="atat")
        # All candidates have wrong middle_voice
        cand_bad = _make_verb("10", "InfEventful", "atat", middle_voice="none")

        import dictionary_pipeline.paths as paths

        original = paths.STATIVE_SHIMS_PATH
        paths.STATIVE_SHIMS_PATH = str(shims_path)

        save_stative_shims(
            validated_verbs=[stative, cand_bad],
            stative_corpus_ids={"10"},
            curated_overrides={},
        )

        paths.STATIVE_SHIMS_PATH = original

        # No compatible candidates → no CSV written
        assert not shims_path.exists()
