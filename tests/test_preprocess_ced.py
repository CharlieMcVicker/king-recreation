import unittest
from king_recreation.preprocess_ced import clean_string, clean_row

class TestPreprocessCed(unittest.TestCase):

    def test_clean_string(self):
        # da1li23yo3hi.2a -> daliyohia -> taliyohia
        self.assertEqual(clean_string("da1li23yo3hi.2a"), "taliyohia")
        # u1ja.3?i1sv23?i -> ujaisvi -> utsaisvi
        self.assertEqual(clean_string("u1ja.3?i1sv23?i"), "utsaisvi")
        self.assertEqual(clean_string("-----"), "")
        self.assertEqual(clean_string(""), "")
        self.assertEqual(clean_string(None), "")

    def test_respell_consonants(self):
        from king_recreation.preprocess_ced import respell_consonants
        # t -> th
        self.assertEqual(respell_consonants("ta"), "tha")
        # d -> t
        self.assertEqual(respell_consonants("da"), "ta")
        # k -> kh
        self.assertEqual(respell_consonants("ka"), "kha")
        # g -> k
        self.assertEqual(respell_consonants("ga"), "ka")
        # complex
        self.assertEqual(respell_consonants("tadig"), "thatik")
        # ts exception
        self.assertEqual(respell_consonants("atsa"), "atsa")
        self.assertEqual(respell_consonants("tsa"), "tsa")
        
        # hl -> lh | _ C
        self.assertEqual(respell_consonants("hla"), "hla") # followed by vowel, no change
        self.assertEqual(respell_consonants("hlta"), "lhtha") # followed by consonant (t->th), change
        
        # hn -> nh | _ C
        self.assertEqual(respell_consonants("hna"), "hna") # followed by vowel, no change
        self.assertEqual(respell_consonants("hnta"), "nhtha") # followed by consonant (t->th), change

    def test_clean_row_basic(self):
        row = {
            "definition": "he's putting on his socks",
            "3rd present": "da1li23yo3hi.2a", # taliyohia -> taliyohi
            "3rd incompletive habitual": "da1li23yo3hi.2ho3?i", # taliyohihoi -> taliyohih
            "3rd completive past": "du1li23yo3hlv23?i", # tuliyohlvi -> tuliyohl
            "2nd imperative": "ta2li3yo2ga", # thaliyoka
            "3rd infinitive": "ju2li23yo3sdi" # juliyosti -> juliyost
        }
        cleaned = clean_row(row)
        self.assertEqual(cleaned["definition"], "he's putting on his socks")
        self.assertEqual(cleaned["present"], "taliyohi")
        self.assertEqual(cleaned["imperfective"], "taliyohih")
        self.assertEqual(cleaned["perfective"], "tuliyohl")
        self.assertEqual(cleaned["imperative"], "thaliyoka")
        self.assertEqual(cleaned["infinitive"], "tsuliyost")

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
        self.assertEqual(cleaned["perfective"], "ulskwat") # ulskwadvi -> ulskwat

    def test_present_vowel_stripping(self):
        # Case: ends in 'a'
        row_a = {"3rd present": "ga1lo1e.2ga"} # galoega -> kaloeka -> kaloek
        self.assertEqual(clean_row(row_a)["present"], "kaloek")
        
        # Case: ends in 'i'
        row_i = {"3rd present": "a1ki1?a"} # akia -> akhia -> akhi (ends in ia)
        self.assertEqual(clean_row(row_i)["present"], "akhi")

        # Case: ends in 'i' but not 'ia'
        row_single_i = {"3rd present": "u1wa1si"} # uwasi -> uwas
        self.assertEqual(clean_row(row_single_i)["present"], "uwas")

        # Case: ends in 'ia'
        row_ia = {"3rd present": "da1li23yo3hi.2a"} # daliyohia -> taliyohia -> taliyohi
        self.assertEqual(clean_row(row_ia)["present"], "taliyohi")

if __name__ == '__main__':
    unittest.main()
