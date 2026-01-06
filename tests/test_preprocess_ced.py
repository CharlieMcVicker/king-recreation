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
        self.assertEqual(cleaned["present"], "daliyohi") # daliyohia -> daliyohi
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

    def test_present_vowel_stripping(self):
        # Case: ends in 'a'
        row_a = {"3rd present": "ga1lo1e.2ga"} # galoega -> galoeg
        self.assertEqual(clean_row(row_a)["present"], "galoeg")
        
        # Case: ends in 'i'
        row_i = {"3rd present": "a1ki1?a"} # akia -> aki (ends in ia)
        # Wait, 'akia' ends in 'ia' -> should be 'aki'
        self.assertEqual(clean_row(row_i)["present"], "aki")

        # Case: ends in 'i' but not 'ia'
        row_single_i = {"3rd present": "u1wa1si"} # uwasi -> uwas
        self.assertEqual(clean_row(row_single_i)["present"], "uwas")

        # Case: ends in 'ia'
        row_ia = {"3rd present": "da1li23yo3hi.2a"} # daliyohia -> daliyohi
        self.assertEqual(clean_row(row_ia)["present"], "daliyohi")

if __name__ == '__main__':
    unittest.main()
