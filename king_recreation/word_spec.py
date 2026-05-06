from dataclasses import dataclass
from typing import Optional, Tuple

from king_recreation.morphemes.prefixes.pronominals import PronominalConfig
from king_recreation.morphology_types import Aspect, Number, Person, PronominalSet

# Re-export Aspect for backward compatibility
__all__ = [
    "Aspect",
    "Person",
    "Number",
    "PronominalSet",
    "WordSpec",
    "FormSpec",
    "calculate_pronominal_key",
]


@dataclass(frozen=True)
class FormSpec:
    aspect: Aspect
    person: Person
    allow_set_a: bool
    stative: bool


@dataclass(frozen=True)
class WordSpec:
    aspect: Aspect
    person: Person
    number: Number
    pronominal_set: PronominalSet
    stative: bool  # True for inherently stative stems (changes pronoun routing)


def calculate_pronominal_key(
    aspect: Aspect, person: Person, config: PronominalConfig, stative: bool
) -> Optional[Tuple[Person, Number, PronominalSet]]:
    """
    Determines the pronominal set components based on grammatical features.
    """
    set_type = (
        config.set_type
    )  # This is already a PronominalSet (will be after config update)
    use_3rd_person_object = config.use_3rd_person_object
    plural = config.plural_pronouns
    number = Number.PLURAL if plural else Number.SINGULAR

    # set_type might still be a string "a" or "b" if config hasn't been updated yet,
    # but we will update PronominalConfig to use the Enum.
    # For now, let's be robust.
    is_set_a = set_type in [PronominalSet.SET_A, "Set A", "a"]

    # Aspect/Stative Logic:
    # Most aspects use the verb's base set (set_a).
    # Perfective and Infinitive force Set B UNLESS the verb is Set A, stative, AND it's not the infinitive.
    target_set_is_a = is_set_a
    if aspect in (Aspect.PERFECTIVE, Aspect.INFINITIVE):
        if not (is_set_a and stative and aspect != Aspect.INFINITIVE):
            target_set_is_a = False

    target_set = PronominalSet.SET_A if target_set_is_a else PronominalSet.SET_B

    if person == Person.FIRST:
        if plural:
            return (Person.FIRST, Number.PLURAL, target_set)
        else:
            if use_3rd_person_object:
                return (
                    Person.FIRST_TO_THIRD,
                    Number.SINGULAR,
                    PronominalSet.PERSON_TO_PERSON,
                )
            else:
                return (Person.FIRST, Number.SINGULAR, target_set)

    if person == Person.SECOND:
        if plural:
            return (Person.SECOND, Number.PLURAL, target_set)
        else:
            if use_3rd_person_object:
                return (
                    Person.SECOND_TO_THIRD,
                    Number.SINGULAR,
                    PronominalSet.PERSON_TO_PERSON,
                )
            else:
                return (Person.SECOND, Number.SINGULAR, target_set)

    if person == Person.THIRD:
        if plural:
            return (Person.THIRD, Number.PLURAL, target_set)
        else:
            return (Person.THIRD, Number.SINGULAR, target_set)

    # Fallback for unexpected person (e.g. if person was empty but aspect was imperative)
    if aspect == Aspect.IMPERATIVE:
        if plural:
            return (Person.SECOND, Number.PLURAL, target_set)
        else:
            if use_3rd_person_object:
                return (
                    Person.SECOND_TO_THIRD,
                    Number.SINGULAR,
                    PronominalSet.PERSON_TO_PERSON,
                )
            else:
                return (Person.SECOND, Number.SINGULAR, target_set)

    return None
