from dataclasses import dataclass
from typing import Optional

from king_recreation.morphemes.prefixes.pronominals import PronominalConfig
from king_recreation.morphology_types import Aspect

# Re-export Aspect for backward compatibility
__all__ = ["Aspect", "WordSpec", "calculate_set_name"]


@dataclass(frozen=True)
class WordSpec:
    aspect: Aspect
    set_name: str  # e.g., "1st Set A", "3pl Set B"
    stative: bool  # True for inherently stative stems (changes pronoun routing)


def calculate_set_name(
    aspect: Aspect, person: str, config: PronominalConfig, stative: bool
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
    if aspect in (Aspect.PERFECTIVE, Aspect.INFINITIVE):
        if not (set_a and stative and aspect != Aspect.INFINITIVE):
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
    if aspect == Aspect.IMPERATIVE:
        if plural:
            return "2pl Set A" if target_set_is_a else "2pl Set B"
        else:
            return (
                "2nd to 3rd"
                if use_3rd_person_object
                else ("2nd Set A" if target_set_is_a else "2nd Set B")
            )

    return None
