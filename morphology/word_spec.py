from dataclasses import dataclass
from enum import Enum

from morphology.morphology_types import (
    Aspect,
    NounStructure,
    Number,
    Person,
    PronominalSet,
)


class SyntacticCategory(Enum):
    NOMINAL = "nominal"
    IMPERATIVE = "imperative"
    VERBY = "verby"


# Re-export morphology types for backward compatibility
__all__ = [
    "Aspect",
    "Person",
    "Number",
    "PronominalSet",
    "NounStructure",
    "WordSpec",
    "SyntacticCategory",
    "get_noun_wordspec",
]

@dataclass(frozen=True)
class WordSpec:
    aspect: Aspect | None = None
    person: Person | None = None
    number: Number | None = None
    pronominal_set: PronominalSet | None = None
    stative: bool = False
    tense_ending: str = ""
    syntactic_category: SyntacticCategory = SyntacticCategory.VERBY


def get_noun_wordspec(
    structure: NounStructure,
    person: Person | None = None,
    number: Number | None = None,
    pronominal_set: PronominalSet | None = None,
) -> WordSpec:
    """
    Constructs a WordSpec from a NounStructure enum based on grammatical mapping rules.
    """
    if structure == NounStructure.ROOT:
        return WordSpec(
            syntactic_category=SyntacticCategory.NOMINAL,
            aspect=None,
            tense_ending="",
            person=person,
            number=number,
            pronominal_set=pronominal_set,
        )
    elif structure == NounStructure.AGENTIVE:
        return WordSpec(
            syntactic_category=SyntacticCategory.NOMINAL,
            aspect=Aspect.IMPERFECTIVE,
            tense_ending="i",
            person=person,
            number=number,
            pronominal_set=pronominal_set,
        )
    elif structure == NounStructure.COMPLETIVE:
        return WordSpec(
            syntactic_category=SyntacticCategory.VERBY,
            aspect=Aspect.PERFECTIVE,
            tense_ending="v'i",
            person=person,
            number=number,
            pronominal_set=pronominal_set,
        )
    elif structure == NounStructure.INCOMPLETIVE:
        return WordSpec(
            syntactic_category=SyntacticCategory.VERBY,
            aspect=Aspect.IMPERFECTIVE,
            tense_ending="o'i",
            person=person,
            number=number,
            pronominal_set=pronominal_set,
        )
    raise ValueError(f"Unknown noun structure: {structure}")


