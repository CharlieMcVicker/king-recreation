import unittest
from king_recreation.preprocess_ced import clean_string, clean_row

class TestPreprocessCed(unittest.TestCase):

    def test_clean_string(self):
        self.assertEqual(clean_string("da1li23yo3hi.2a"), "daliyohia")
        self.assertEqual(clean_string("u1ja.3?i1sv23?i"), "ujaisvi")
        self.assertEqual(clean_string("-----"), "")
        self.assertEqual(clean_string(""), "")
        self.assertEqual(clean_string(None), "")

    def test_clean_row_basic(self):
        row = {
            "definition": "he's putting on his socks",
            "3rd present": "da1li23yo3hi.2a",
            "3rd incompletive habitual": "da1li23yo3hi.2ho3?i",
            "3rd completive past": "du1li23yo3hlv23?i",
            "2nd imperative": "ta2li3yo2ga",
            "3rd infinitive": "ju2li23yo3sdi"
        }
        cleaned = clean_row(row)
        self.assertEqual(cleaned["definition"], "he's putting on his socks")
        self.assertEqual(cleaned["present"], "daliyohia")
        self.assertEqual(cleaned["imperfective"], "daliyohih") # daliyohihoi -> daliyohih
        self.assertEqual(cleaned["perfective"], "duliyohl") # duliyohlvi -> duliyohl
        self.assertEqual(cleaned["imperative"], "taliyoga")
        self.assertEqual(cleaned["infinitive"], "juliyosd") # juliyosdi -> juliyosd

    def test_clean_row_missing(self):
        row = {
            "definition": "it's ending",
            "3rd present": "al1sgwa.2di.3?a",
            "3rd incompletive habitual": "al1sgwa.2di32sgo3?i",
            "3rd completive past": "ul1sgwa.3dv23?i",
            "2nd imperative": "-----",
            "3rd infinitive": "ul2sgwa.2di1sdi"
        }
        cleaned = clean_row(row)
        self.assertEqual(cleaned["imperative"], "")
        self.assertEqual(cleaned["perfective"], "ulsgwad") # ulsgwadv(i) -> ulsgwad after stripping vi

if __name__ == '__main__':
    unittest.main()
