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
    original_data: dict[str, str] | None = None,
) -> DictionaryVerb:
    """Create a minimal DictionaryVerb for testing."""
    data: dict[str, str] = original_data or {
        "corpus_id": corpus_id,
        "prediction": prediction,
        "class": cls,
        "h_grade": h_grade,
        "g_grade": "",
        "post_root_morpheme": "",
        "set_a_b": "a",
        "stem_type": stem_type,
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

    meta = PredictionMeta(
        corpus_id=corpus_id,
        definition=data.get("definition", "to go"),
        entry_no=data.get("entry_no", "1"),
        prediction=Prediction(prediction),
    )
    config = PrefixConfig.from_row(data)
    morphology = MorphologicalVerb(
        h_grade_root=h_grade,
        glottal_grade_root=None,
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
