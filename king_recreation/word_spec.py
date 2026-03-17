import logging
from dataclasses import dataclass
from typing import Optional

from king_recreation.morphemes.prefixes.pronominals import PronominalConfig


@dataclass(frozen=True)
class WordSpec:
    aspect: str  # e.g., "present", "perfective", "imperative"
    set_name: str  # e.g., "1st Set A", "3pl Set B"
    stative: bool  # True for inherently stative stems (changes pronoun routing)


FORM_NAME_TO_PERSON = {
    "present": "3rd",
    "imperfective": "3rd",
    "perfective": "3rd",
    "infinitive": "3rd",
    "imperative": "2nd",
    "present_1sg": "1st",
}

FORM_NAME_TO_ASPECT = {
    "present": "present",
    "present_1sg": "present",
    "imperfective": "imperfective",
    "perfective": "perfective",
    "imperative": "imperative",
    "infinitive": "infinitive",
}


def build_wordspec(form_name: str, config: PronominalConfig, stative: bool) -> WordSpec:
    """
    Acts as the explicit boundary between implicit dictionary schemas and
    concrete morphology requirements.
    """
    person = FORM_NAME_TO_PERSON.get(form_name, "3rd")
    aspect = FORM_NAME_TO_ASPECT.get(form_name, form_name)
    set_name = calculate_set_name(aspect, person, config, stative)

    if not set_name:
        logging.getLogger(__name__).warning(
            f"No Set Name resolvable for {form_name}. Falling back to 3rd Set A"
        )
        set_name = "3rd Set A"

    return WordSpec(aspect=aspect, set_name=set_name, stative=stative)


def calculate_set_name(
    aspect: str, person: str, config: PronominalConfig, stative: bool
) -> Optional[str]:
    """
    Determines the pronominal set name based on grammatical features.
    Migrated from pronominals.py -> get_pronominal_set_name
    """
    set_type = config.set_type
    use_3rd_person_object = config.use_3rd_person_object
    plural = config.plural_pronouns
    set_a = set_type in ["Set A", "a"]

    # Aspect/Stative Logic:
    # Most aspects use the verb's base set (set_a).
    # Perfective and Infinitive force Set B UNLESS the verb is Set A, stative, AND it's not the infinitive.
    target_set_is_a = set_a
    if aspect in ["perfective", "infinitive"]:
        if not (set_a and stative and aspect != "infinitive"):
            target_set_is_a = False

    if person == "1st":
        if plural:
            return "1pl Set A" if target_set_is_a else "1pl Set B"
        else:
            return (
                "1st to 3rd"
                if use_3rd_person_object
                else ("1st Set A" if target_set_is_a else "1st Set B")
            )

    if person == "2nd":
        if plural:
            return "2pl Set A" if target_set_is_a else "2pl Set B"
        else:
            return (
                "2nd to 3rd"
                if use_3rd_person_object
                else ("2nd Set A" if target_set_is_a else "2nd Set B")
            )

    if person == "3rd":
        if plural:
            return "3pl Set A" if target_set_is_a else "3pl Set B"
        else:
            return "3rd Set A" if target_set_is_a else "3rd Set B"

    # Fallback for unexpected person (e.g. if person was empty but aspect was imperative)
    if aspect == "imperative":
        if plural:
            return "2pl Set A" if target_set_is_a else "2pl Set B"
        else:
            return (
                "2nd to 3rd"
                if use_3rd_person_object
                else ("2nd Set A" if target_set_is_a else "2nd Set B")
            )

    return None
