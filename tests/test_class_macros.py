import os
import tempfile

from king_recreation.morphemes.aspect.pattern_registry import PatternRegistry


def test_macro_expansion():
    # Mock CSV data
    csv_content = """class,stem final,present,imperfective,perfective,imperative,infinitive
hvsk,,hvsk,hvsk,nh;han,hvka,ht;*ht;hvst
"""

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        registry = PatternRegistry()
        registry.load_from_csv(temp_path)
        patterns = {p.name: p for p in registry.expanded_patterns}

        # Expected variants (Cartesian product of 2 perfective x 3 infinitive = 6)
        expected_names = [
            "hvsk",
            "hvsk[inf2]",
            "hvsk[inf3]",
            "hvsk[perf2]",
            "hvsk[perf2-inf2]",
            "hvsk[perf2-inf3]",
        ]

        assert len(patterns) == 6
        for name in expected_names:
            assert name in patterns

        # Verify specific values for a complex one
        # Note: the shorthands in class_patterns.py are:
        # "present": "pres", "imperfective": "imperf", "perfective": "perf", "imperative": "imp", "infinitive": "inf"
        # hvsk[perf2-inf3] means perfective variant 2 ("han") and infinitive variant 3 ("hvst")
        p = patterns["hvsk[perf2-inf3]"]
        assert p.perfective == "han"
        assert p.infinitive == "hvst"
        assert p.present == "hvsk"

        # Verify first one (base)
        pbase = patterns["hvsk"]
        assert pbase.perfective == "nh"
        assert pbase.infinitive == "ht"

    finally:
        os.remove(temp_path)
