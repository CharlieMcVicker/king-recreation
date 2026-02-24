import pytest

from king_recreation.morphemes.post_root_morphemes import (
    PostRootMorpheme,
    PostRootMorphemeRegistry,
    match_post_root_morphemes,
)


@pytest.fixture
def mock_registry(monkeypatch):
    """
    Manually inject morphemes into the registry for testing.
    """
    reg = PostRootMorphemeRegistry.get_instance()

    # Mock morphemes
    m1 = PostRootMorpheme(name="become-long[a]", form="a", classes=["become[*]"])
    m2 = PostRootMorpheme(name="iterative", form="ihs", classes=["cause[perf2]"])
    m3 = PostRootMorpheme(name="leaving", form="iy", classes=["a"])

    reg.morphemes = [m1, m2, m3]
    reg.morphemes_by_name = {m.name: m for m in reg.morphemes}
    reg.class_map = reg.create_class_map()
    return reg


def test_match_wildcard_become(mock_registry):
    # Tests that become[perf2] matches become[*]
    row = {"class": "become[perf2]", "h_grade": "uwesv'a", "g_grade": "uwesv'a"}
    results = match_post_root_morphemes(row)

    # results[0] is original, results[1+] are matches
    assert len(results) == 2
    match = results[1]
    assert match["post_root_morpheme"] == "become-long[a]"
    assert match["h_grade"] == "uwesv'"
    assert match["g_grade"] == "uwesv'"


def test_match_exact_class(mock_registry):
    # Tests that cause[perf2] matches iterative
    row = {"class": "cause[perf2]", "h_grade": "duyelihs", "g_grade": "duyelihs"}
    results = match_post_root_morphemes(row)

    assert len(results) == 2
    match = results[1]
    assert match["post_root_morpheme"] == "iterative"
    assert match["h_grade"] == "duyel"
    assert match["g_grade"] == "duyel"


def test_no_match_if_class_differs(mock_registry):
    # Tests that become[perf2] does NOT match iterative (cause[perf2])
    row = {"class": "become[perf2]", "h_grade": "uwesv'a", "g_grade": "uwesv'a"}
    results = match_post_root_morphemes(row)

    # Should only return the original row
    assert len(results) == 2  # Still matches become[*] but not cause[perf2]
    for r in results[1:]:
        assert r["post_root_morpheme"] != "iterative"


def test_multiple_matches(mock_registry):
    # If a class matches multiple rules (unlikely in current data but supported by code)
    # Let's add an exact match rule that also fits
    mock_registry.morphemes.append(
        PostRootMorpheme(name="become-exact", form="a", classes=["become[perf2]"])
    )
    mock_registry.morphemes_by_name = {m.name: m for m in mock_registry.morphemes}
    mock_registry.class_map = mock_registry.create_class_map()

    row = {"class": "become[perf2]", "h_grade": "uwesv'a", "g_grade": "uwesv'a"}
    results = match_post_root_morphemes(row)

    # 1 original + 1 wildcard + 1 exact
    assert len(results) == 3
    morphemes = [r.get("post_root_morpheme") for r in results]
    assert "become-long[a]" in morphemes
    assert "become-exact" in morphemes


def test_no_suffix_match_break(mock_registry):
    # If the class matches but the form doesn't end with the suffix
    row = {
        "class": "become[perf2]",
        "h_grade": "uwesv'x",  # does not end in 'a'
        "g_grade": "uwesv'a",
    }
    results = match_post_root_morphemes(row)

    # Should only return the original row because truncation failed
    assert len(results) == 1
