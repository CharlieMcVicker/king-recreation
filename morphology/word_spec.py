from dataclasses import dataclass

from morphology.morphology_types import Aspect, Number, Person, PronominalSet

# Re-export Aspect for backward compatibility
__all__ = [
    "Aspect",
    "Person",
    "Number",
    "PronominalSet",
    "WordSpec",
]


@dataclass(frozen=True)
class WordSpec:
    aspect: Aspect
    person: Person
    number: Number
    pronominal_set: PronominalSet
    stative: bool  # True for inherently stative stems (changes pronoun routing)
    tense_ending: str = ""
