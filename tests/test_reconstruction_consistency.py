import unittest
from king_recreation.stem_analysis import check_root_consistency


class TestReconstructionConsistency(unittest.TestCase):
    def test_class_ia_star(self):
        # "he's catching a falling person, object"
        # IA* endings: present="", imperfective="sk", perfective="s", imperative="*aki", infinitive="st"
        class_info = {
            "present": "",
            "imperfective": "sk",
            "perfective": "s",
            "imperative": "*aki",
            "infinitive": "st",
        }
        stem_row = {
            "present": "skwahle",
            "imperfective": "skwahlesk",
            "perfective": "skwahles",
            "imperative": "skwahlaki",
            "infinitive": "skwahlest",
        }
        consistent, root, details = check_root_consistency(stem_row, class_info)
        self.assertTrue(consistent, f"Should be consistent. Details: {details}")
        self.assertEqual(root, "skwahle")

    def test_class_iiia2(self):
        # "He is getting in a car, box, etc"
        # IIIa2 endings: sk, sk, *n, ka, @ht
        class_info = {
            "present": "sk",
            "imperfective": "sk",
            "perfective": "*n",
            "imperative": "ka",
            "infinitive": "@ht",
        }
        stem_row = {
            "present": "atsavsk",
            "imperfective": "atsavsk",
            "perfective": "atsan",
            "imperative": "atsavka",
            "infinitive": "atsht",  # 'ats' is 2-char truncation of 'atsav'
        }
        consistent, root, details = check_root_consistency(stem_row, class_info)
        self.assertTrue(consistent, f"Should be consistent. Details: {details}")
        self.assertEqual(root, "atsav")

    def test_inconsistency_wrong_truncation(self):
        class_info = {"present": "", "imperative": "*aki"}
        # Present: WALK, Imperative: WALKaki (no truncation applied)
        stem_row = {"present": "WALK", "imperative": "WALKaki"}
        # get_root_candidate("WALKaki", "*aki") -> "WALK" -> strip 1 -> "WAL"
        # "WAL" != "WALK" -> inconsistent
        consistent, root, details = check_root_consistency(stem_row, class_info)
        self.assertFalse(consistent)
        self.assertIn("imperative: Truncation mismatch", details[0])

    def test_inconsistency_different_stems(self):
        class_info = {"present": "", "perfective": "s"}
        stem_row = {"present": "WALK", "perfective": "RUNs"}
        consistent, root, details = check_root_consistency(stem_row, class_info)
        self.assertFalse(consistent)
        self.assertIn("perfective: Root mismatch", details[0])


if __name__ == "__main__":
    unittest.main()
