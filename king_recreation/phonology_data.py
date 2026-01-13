from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional

class StemType(Enum):
    CONSONANT = 'con'
    VOWEL_A = 'vowel_a'
    VOWEL_E = 'vowel_e'
    VOWEL_O = 'vowel_o'
    VOWEL_U = 'vowel_u'
    VOWEL_V = 'vowel_v'
    VOWEL_I = 'vowel_i'
    ASPIRATED = 'aspirated' # th-
    S_STEM = 's_stem'       # s-
    # Note: Metathesis is handled by Strategy, but StemType identifies initial sound

class MetathesisStrategy(Enum):
    NONE = 'none'
    H_CONS = 'h_cons'      # kha- / tsha- / akhi-
    VOWEL = 'vowel'        # kh- / h- / uhw- / ...

@dataclass(frozen=True)
class PrePronominalConfig:
    translocutive: bool = False
    partitive: bool = False
    distributive: bool = False

@dataclass(frozen=True)
class PronominalConfig:
    set_type: str  # 'a' or 'b'
    stem_type: StemType
    metathesis_strategy: MetathesisStrategy = MetathesisStrategy.NONE
    
    # Flags for prefix variants
    use_ka_variant: bool = False       # 3rd Set A: ka-/k- (True) vs a-/ø (False)
    use_uwa_for_3rd_set_b: bool = False # 3rd Set B: uwa- vs u- (on consonants)
    use_aki_for_1st_set_b: bool = False # 1st Set B: aki- vs ak- (on consonants)

def get_stem_type(stem: str) -> StemType:
    if not stem: return StemType.CONSONANT
    if stem.startswith('th'): return StemType.ASPIRATED
    if stem.startswith('s') and len(stem) > 1 and stem[1] not in get_vowel_set():
        return StemType.S_STEM
    
    char = stem[0]
    if char == 'a': return StemType.VOWEL_A
    if char == 'e': return StemType.VOWEL_E
    if char == 'i': return StemType.VOWEL_I
    if char == 'o': return StemType.VOWEL_O
    if char == 'u': return StemType.VOWEL_U
    if char == 'v': return StemType.VOWEL_V
    return StemType.CONSONANT

def get_prefix_for_config(set_name: str, config: PronominalConfig) -> str:
    s_type = config.stem_type
    meta = config.metathesis_strategy
    
    # helper for non-vowel check
    is_con = s_type in [StemType.CONSONANT, StemType.ASPIRATED, StemType.S_STEM]
    
    # Metathesis prefixes (some are special, others are base + restoration)
    if meta == MetathesisStrategy.H_CONS:
        if set_name == '3rd Set A': return 'kha-'
        if set_name == '2nd Set B': return 'tsha-'
        if set_name == '1st Set B': return 'akhi-'
        # Others (Set B 3rd, Set A 2nd/1st) use base + h restoration
        
    if meta == MetathesisStrategy.VOWEL:
        if set_name == '3rd Set A': return 'kh-'
        if set_name == '3rd Set B': return 'uhw-'
        if set_name == '2nd Set A': return 'h-'
    
    if set_name == '3rd Set A':
        if config.use_ka_variant:
            return 'ka-' if is_con else 'k-'
        else: # Standard variant
            if is_con or s_type == StemType.VOWEL_A: return 'a-'
            return '' # ø for other vowels (e, i, o, u, v)
            
    if set_name == '3rd Set B':
        if s_type == StemType.VOWEL_A: return 'u-' # u- replaces a
        if s_type == StemType.VOWEL_V: return 'uwa-'
        if s_type in [StemType.VOWEL_E, StemType.VOWEL_I, StemType.VOWEL_O, StemType.VOWEL_U]:
             return 'uw-'
        if is_con:
             return 'uwa-' if config.use_uwa_for_3rd_set_b else 'u-'
             
    if set_name == '2nd Set B':
        if s_type == StemType.ASPIRATED: return 'ts-'
        if s_type == StemType.S_STEM: return 't-'
        if is_con: return 'tsa-'
        return 'ts-' # Vowels
        
    if set_name == '2nd Set A':
        if is_con: return 'hi-'
        return 'h-' # Vowels
        
    if set_name == '2nd to 3rd':
        if is_con: return 'hi-'
        return 'hiy-'
        
    if set_name == '1st Set A':
        if is_con: return 'tsi-'
        return 'k-' 
        
    if set_name == '1st Set B':
        if s_type == StemType.ASPIRATED or s_type == StemType.S_STEM: return 'akh-'
        if is_con: 
            return 'aki-' if config.use_aki_for_1st_set_b else 'ak-'
        return 'akw-' # Vowels
        
    if set_name == '1st to 3rd':
        if is_con: return 'tsi-'
        return 'tsiy-'

    return ''


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
        ('ts-', Condition.VOWEL),
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

def is_h_dropping_set(set_name):
    return set_name in ['2nd to 3rd', '1st to 3rd', '1st Set A']

def drop_first_h(stem: str) -> str:
    """
    Removes the first 'h' found in the stem.
    Used for h-dropping sets validation.
    """
    idx = stem.find('h')
    if idx != -1:
        return stem[:idx] + stem[idx+1:]
    return stem
