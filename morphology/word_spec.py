from dataclasses import dataclass

from morphology.morphology_types import (
    Aspect,
    NounStructure,
    Number,
    Person,
    PronominalSet,
)

# Re-export morphology types for backward compatibility
__all__ = [
    "Aspect",
    "Person",
    "Number",
    "PronominalSet",
    "NounStructure",
    "WordSpec",
]

NOUN_SUFFIX_RULES = {
    NounStructure.ROOT: "",
    NounStructure.AGENTIVE: "i",
    NounStructure.COMPLETIVE: "v'i",
    NounStructure.INCOMPLETIVE: "o'i",
}

NOUN_ASPECT_MAPPING = {
    NounStructure.ROOT: None,
    NounStructure.AGENTIVE: Aspect.IMPERFECTIVE,
    NounStructure.COMPLETIVE: Aspect.PERFECTIVE,
    NounStructure.INCOMPLETIVE: Aspect.IMPERFECTIVE,
}


@dataclass(frozen=True)
class WordSpec:
    aspect: Aspect | None = None
    person: Person | None = None
    number: Number | None = None
    pronominal_set: PronominalSet | None = None
    stative: bool = False
    tense_ending: str = ""
    noun_structure: NounStructure | None = None

    @property
    def noun_suffix(self) -> str:
        if self.noun_structure is None:
            return ""
        return NOUN_SUFFIX_RULES.get(self.noun_structure, "")

    @property
    def noun_aspect(self) -> Aspect | None:
        if self.noun_structure is None:
            return None
        return NOUN_ASPECT_MAPPING.get(self.noun_structure)
