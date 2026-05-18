"""
Bridge between dictionary column schemas and the morphological WordSpec system.

This module owns the mapping from dictionary form names (column headers like
"present", "present_1sg") to morphological concepts (Aspect, person).

Dictionary-pipeline modules should import from here.
Morphological-core modules should import from word_spec directly.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from morphology.morphemes.prefixes.pronominals import PronominalConfig
from morphology.reconstruction import MorphologicalVerb
from morphology.word_spec import (
    Aspect,
    FormSpec,
    Number,
    Person,
    PronominalSet,
    WordSpec,
    calculate_pronominal_key,
)

# ... (existing mappings)


class Prediction(str, Enum):
    """
    Enum saying which fields of a verb are being modeled in a given
    derivation
    """

    FULL_EVENTFUL = "FullEventful"
    """Attempts to predice all forms for a standard five-aspect verb"""


@dataclass
class DictionaryVerb:
    definition: str
    morphology: MorphologicalVerb
    corpus_id: int | None = None
    entry_no: int | None = None
    derivations: list["DictionaryVerb"] = field(default_factory=list)
    original_data: dict[str, Any] = field(
        default_factory=dict, repr=False, hash=False, compare=False
    )
    segmented_forms: dict[str, str] = field(
        default_factory=dict,
    )
    user_selected: bool = False

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "DictionaryVerb":
        clean_data = data.copy()
        if "morphology" in clean_data:
            clean_data["morphology"] = MorphologicalVerb.from_dict(
                clean_data["morphology"]
            )
        if "derivations" in clean_data:
            clean_data["derivations"] = [
                DictionaryVerb.from_dict(d) for d in clean_data["derivations"]
            ]
        if "corpus_id" in clean_data and clean_data["corpus_id"] is not None:
            clean_data["corpus_id"] = int(clean_data["corpus_id"])
        if "entry_no" in clean_data and clean_data["entry_no"] is not None:
            clean_data["entry_no"] = int(clean_data["entry_no"])
        return DictionaryVerb(**clean_data)


# Dictionary column name -> morphological Aspect
FORM_NAME_TO_ASPECT: dict[str, Aspect] = {
    "present": Aspect.PRESENT,
    "present_1sg": Aspect.PRESENT,
    "imperfective": Aspect.IMPERFECTIVE,
    "perfective": Aspect.PERFECTIVE,
    "imperative": Aspect.IMPERATIVE,
    "infinitive": Aspect.INFINITIVE,
}

# Dictionary column name -> grammatical person
FORM_NAME_TO_PERSON: dict[str, Person] = {
    "present": Person.THIRD,
    "imperfective": Person.THIRD,
    "perfective": Person.THIRD,
    "infinitive": Person.THIRD,
    "imperative": Person.SECOND,
    "present_1sg": Person.FIRST,
}


FORM_NAMES_FOR_PREDICTION = {
    Prediction.FULL_EVENTFUL: [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
}

# All dictionary form columns (for iterating over dictionary rows)
ALL_FORM_NAMES = FORM_NAMES_FOR_PREDICTION[Prediction.FULL_EVENTFUL]


def get_form_spec(form_name: str) -> FormSpec:
    """
    Bridge function: converts a dictionary form_name into a FormSpec.
    Currently hardcoded for Scope.EVENTFUL as per Phase 1 plan.
    """
    person = FORM_NAME_TO_PERSON.get(form_name, Person.THIRD)
    aspect = FORM_NAME_TO_ASPECT.get(form_name, Aspect.PRESENT)

    # Maintain current behavior: PERFECTIVE and INFINITIVE force Set B
    allow_set_a = aspect not in (Aspect.PERFECTIVE, Aspect.INFINITIVE)

    return FormSpec(
        aspect=aspect,
        person=person,
        allow_set_a=allow_set_a,
        stative=False,  # This will be overridden in build_wordspec
    )


def build_wordspec(form_name: str, config: PronominalConfig, stative: bool) -> WordSpec:
    """
    Bridge function: converts a dictionary form_name into a WordSpec.
    """
    form_spec = get_form_spec(form_name)
    # Enrich with stative info from the verb
    form_spec = FormSpec(
        aspect=form_spec.aspect,
        person=form_spec.person,
        allow_set_a=form_spec.allow_set_a,
        stative=stative,
    )

    key = calculate_pronominal_key(
        form_spec.aspect, form_spec.person, config, form_spec.stative
    )

    if not key:
        logging.getLogger(__name__).warning(
            f"No Pronominal Key resolvable for {form_name}. Falling back to 3rd Set A"
        )
        person, number, p_set = Person.THIRD, Number.SINGULAR, PronominalSet.SET_A
    else:
        person, number, p_set = key

    return WordSpec(
        aspect=form_spec.aspect,
        person=person,
        number=number,
        pronominal_set=p_set,
        stative=stative,
    )
