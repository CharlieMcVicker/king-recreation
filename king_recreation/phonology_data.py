from enum import Enum

class Condition(Enum):
    VOWEL_AE = 'vowel_ae'
    VOWEL = 'vowel'
    CONSONANT = 'con'
    A_REPLACE = 'a_replace'
    VOWEL_NO_A = 'vowel_no_a'
    V = 'v'
    ASPIRATED = 'aspirated'
    S_STEM = 's_stem'
    METATHESIS_H_CONS = 'metathesis_h_cons'
    METATHESIS_VOWEL = 'metathesis_vowel'

def get_vowel_set():
    return {'a', 'e', 'o', 'u', 'v', 'i'}

VOWEL_SET = get_vowel_set()

PRONOMINAL_PREFIXES_MAP = {
    '3rd Set A': [
        ('kha-', Condition.METATHESIS_H_CONS),
        ('kh-', Condition.METATHESIS_VOWEL),
        ('ø', Condition.VOWEL_AE),
        ('k-', Condition.VOWEL),
        ('a-', Condition.CONSONANT),
        ('ka-', Condition.CONSONANT)
    ],
    '3rd Set B': [
        ('uhw-', Condition.METATHESIS_VOWEL),
        ('uw-', Condition.VOWEL_NO_A),
        ('uwa-', Condition.V),
        ('u-', Condition.CONSONANT),
        ('uwa-', Condition.CONSONANT),
        ('u-', Condition.A_REPLACE)
    ],
    '2nd Set B': [
        ('ts-', Condition.VOWEL),
        ('tsa-', Condition.CONSONANT),
        ('tsha-', Condition.METATHESIS_H_CONS),
        ('ts-', Condition.ASPIRATED),
        ('t-', Condition.S_STEM)
    ],
    '2nd Set A': [
        ('h-', Condition.METATHESIS_VOWEL),
        ('h-', Condition.VOWEL),
        ('hi-', Condition.CONSONANT)
    ],
    '2nd to 3rd': [
        ('hiy-', Condition.VOWEL),
        ('hi-', Condition.CONSONANT)
    ],
    '1st Set A': [
        ('tsi-', Condition.CONSONANT),
        ('k-', Condition.VOWEL)
    ],
    '1st Set B': [
        ('aki-', Condition.CONSONANT),
        ('akw-', Condition.VOWEL),
        ('akh-', Condition.ASPIRATED), 
        ('akh-', Condition.S_STEM),
        ('akhi-', Condition.METATHESIS_H_CONS),
        ('ak-', Condition.CONSONANT) 
    ],
    '1st to 3rd': [
        ('tsi-', Condition.CONSONANT),
        ('tsiy-', Condition.VOWEL)
    ]
}

def get_pronominal_set_name(form_name, set_type, imp_type):
    if form_name == 'present':
        return '3rd Set A' if set_type == 'Set A' or set_type == 'a' else '3rd Set B'
    if form_name == 'imperfective':
        return '3rd Set A' if set_type == 'Set A' or set_type == 'a' else '3rd Set B'
    if form_name == 'perfective':
        return '3rd Set B'
    if form_name == 'imperative':
        return '2nd to 3rd' if imp_type == 'to_3rd' else ('2nd Set A' if (set_type == 'Set A' or set_type == 'a') else '2nd Set B')
    if form_name == 'infinitive':
        return '3rd Set B'
    if form_name == 'present_1sg':
        if imp_type == 'to_3rd':
            return '1st to 3rd'
        return '1st Set A' if (set_type == 'Set A' or set_type == 'a') else '1st Set B'
    return None
