"""
Bridge between dictionary column schemas and the morphological WordSpec system.

This module owns the mapping from dictionary form names (column headers like
"present", "present_1sg") to morphological concepts (Aspect, person).

Dictionary-pipeline modules should import from here.
Morphological-core modules should import from word_spec directly.
"""

import logging
from typing import Dict

from king_recreation.morphemes.prefixes.pronominals import PronominalConfig
from king_recreation.word_spec import Aspect, WordSpec, calculate_set_name

# Dictionary column name -> morphological Aspect
FORM_NAME_TO_ASPECT: Dict[str, Aspect] = {
    "present": Aspect.PRESENT,
    "present_1sg": Aspect.PRESENT,
    "imperfective": Aspect.IMPERFECTIVE,
    "perfective": Aspect.PERFECTIVE,
    "imperative": Aspect.IMPERATIVE,
    "infinitive": Aspect.INFINITIVE,
}

# Dictionary column name -> grammatical person
FORM_NAME_TO_PERSON: Dict[str, str] = {
    "present": "3rd",
    "imperfective": "3rd",
    "perfective": "3rd",
    "infinitive": "3rd",
    "imperative": "2nd",
    "present_1sg": "1st",
}

# All dictionary form columns (for iterating over dictionary rows)
ALL_FORM_NAMES = [
    "present",
    "present_1sg",
    "imperfective",
    "perfective",
    "imperative",
    "infinitive",
]

# Aspect-only forms (no person variants like present_1sg)
ASPECT_FORM_NAMES = [
    "present",
    "imperfective",
    "perfective",
    "imperative",
    "infinitive",
]


def build_wordspec(form_name: str, config: PronominalConfig, stative: bool) -> WordSpec:
    """
    Bridge function: converts a dictionary form_name into a WordSpec.

    This is the explicit boundary between dictionary column names
    and concrete morphology requirements.
    """
    person = FORM_NAME_TO_PERSON.get(form_name, "3rd")
    aspect = FORM_NAME_TO_ASPECT.get(form_name)
    if aspect is None:
        # Fallback: try to parse the form name as an Aspect value directly
        try:
            aspect = Aspect(form_name)
        except ValueError:
            logging.getLogger(__name__).warning(
                f"Unknown form_name '{form_name}', defaulting to PRESENT"
            )
            aspect = Aspect.PRESENT

    set_name = calculate_set_name(aspect, person, config, stative)

    if not set_name:
        logging.getLogger(__name__).warning(
            f"No Set Name resolvable for {form_name}. Falling back to 3rd Set A"
        )
        set_name = "3rd Set A"

    return WordSpec(aspect=aspect, set_name=set_name, stative=stative)
