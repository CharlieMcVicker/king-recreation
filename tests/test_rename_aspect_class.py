import json
import os
import tempfile
import unittest

from scripts.rename_aspect_class import ParentClassGroupRule, parse_mapping_file


class TestRenameAspectClass(unittest.TestCase):
    def test_parent_class_group_rule(self):
        # Rule renaming parent class 'hvsk' to 'hvsg' with specific subclass renames
        rule = ParentClassGroupRule("hvsk", "hvsg", {"nh": "hn", "han": "han"})

        # Split matching & transformation
        self.assertTrue(rule.matches_split("hvsk", "nh"))
        self.assertTrue(rule.matches_split("hvsk", "han"))
        self.assertTrue(rule.matches_split("hvsk", "other"))
        self.assertFalse(rule.matches_split("sk-h", "nh"))

        self.assertEqual(rule.transform_split("hvsk", "nh"), ("hvsg", "hn"))
        self.assertEqual(rule.transform_split("hvsk", "other"), ("hvsg", "other"))

        # Joined matching & transformation
        self.assertTrue(rule.matches_joined("hvsk-nh"))
        self.assertTrue(rule.matches_joined("hvsk-nh[perf2]"))
        self.assertTrue(rule.matches_joined("hvsk-other"))

        self.assertEqual(rule.transform_joined("hvsk-nh"), "hvsg-hn")
        self.assertEqual(rule.transform_joined("hvsk-nh[perf2]"), "hvsg-hn[perf2]")
        self.assertEqual(rule.transform_joined("hvsk-other"), "hvsg-other")

    def test_parse_mapping_file_structured(self):
        data = [
            {"old": "hvsk", "new": "hvsg", "subclasses": {"nh": "hn", "han": "han"}}
        ]
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json") as tmp:
            json.dump(data, tmp)
            tmp_path = tmp.name

        try:
            rules = parse_mapping_file(tmp_path)
            self.assertEqual(len(rules), 1)
            r = rules[0]
            self.assertEqual(r.old_class, "hvsk")
            self.assertEqual(r.new_class, "hvsg")
            self.assertEqual(r.subclasses_map["nh"], "hn")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
