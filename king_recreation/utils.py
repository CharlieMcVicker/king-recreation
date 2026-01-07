import re

def get_class_sort_key(class_name):
    """
    Returns a sort key for King's verb classes.
    Regex handles partial classes (like 'Ia' or 'X') by making letter and number optional.
    
    Classes are sorted by:
    1. Roman numeral (I-X)
    2. Lowercase letter (a-d)
    3. Number (1-3)
    
    Example: Ia, Ib, IIa, IIa1, IIa2, X
    """
    if not class_name:
        return (99, '', 0)
        
    match = re.match(r'^([IVX]+)([a-z]?)(\d*)$', class_name)
    if not match:
        return (99, class_name, 0)
        
    roman, letter, number = match.groups()
    
    roman_map = {
        'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5,
        'VI': 6, 'VII': 7, 'VIII': 8, 'IX': 9, 'X': 10
    }
    
    roman_val = roman_map.get(roman, 99)
    number_val = int(number) if number else 0
    
    return (roman_val, letter, number_val)
