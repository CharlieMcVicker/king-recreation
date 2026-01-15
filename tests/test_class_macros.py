import io
import csv
from king_recreation.class_patterns import ClassPatterns


def test_macro_expansion():
    # Mock CSV data
    csv_content = """class,stem final,present,imperfective,perfective,imperative,infinitive
hvsk,,hvsk,hvsk,nh;han,hvka,ht;*ht;hvst
"""

    # We need to mock the file reading part or use a temporary file
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write(csv_content)
        temp_path = f.name

    try:
        patterns = ClassPatterns.from_csv(temp_path)

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


if __name__ == "__main__":
    test_macro_expansion()
    print("Test passed!")
