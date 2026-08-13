import os
import tempfile
import unittest

from scripts.rename_aspect_class import (
    build_replacement_patterns,
    process_file,
    replace_in_value,
)


class TestRenameAspectClass(unittest.TestCase):
    def test_pattern_matching_exact_and_subvariants(self):
        renames = {"sk-s": "sk-s-new", "go-in": "go-in-new"}
        patterns = build_replacement_patterns(renames)

        # Exact match
        val, changed = replace_in_value("sk-s", patterns)
        self.assertTrue(changed)
        self.assertEqual(val, "sk-s-new")

        # Bracketed subvariant match
        val, changed = replace_in_value("sk-s[hi-hihst]", patterns)
        self.assertTrue(changed)
        self.assertEqual(val, "sk-s-new[hi-hihst]")

        # Hyphenated subclass match (e.g. sk-s-hi-hihst or sk-s-a[inf2])
        val, changed = replace_in_value("sk-s-hi-hihst", patterns)
        self.assertTrue(changed)
        self.assertEqual(val, "sk-s-new-hi-hihst")

        val, changed = replace_in_value("sk-s-a[inf2]", patterns)
        self.assertTrue(changed)
        self.assertEqual(val, "sk-s-new-a[inf2]")

        # Non-matching prefix
        val, changed = replace_in_value("sk-other", patterns)
        self.assertFalse(changed)
        self.assertEqual(val, "sk-other")

    def test_process_file(self):
        renames = {"cause": "cause-renamed"}
        patterns = build_replacement_patterns(renames)

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
            tmp.write("corpus_id,class,from_class,to_class\n")
            tmp.write("1,cause,cause[perf2],g-ts\n")
            tmp.write("2,cause[perf3],g-ts,cause\n")
            tmp_path = tmp.name

        try:
            # Dry run test
            counts = process_file(
                tmp_path, ["class", "from_class", "to_class"], patterns, dry_run=True
            )
            self.assertEqual(counts["class"], 2)
            self.assertEqual(counts["from_class"], 1)
            self.assertEqual(counts["to_class"], 1)

            # Verify file wasn't changed on dry run
            with open(tmp_path, "r") as f:
                content = f.read()
            self.assertIn("1,cause,cause[perf2],g-ts", content)

            # Actual run
            counts = process_file(
                tmp_path, ["class", "from_class", "to_class"], patterns, dry_run=False
            )
            with open(tmp_path, "r") as f:
                lines = f.readlines()
            self.assertEqual(
                lines[1].strip(), "1,cause-renamed,cause-renamed[perf2],g-ts"
            )
            self.assertEqual(
                lines[2].strip(), "2,cause-renamed[perf3],g-ts,cause-renamed"
            )
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
