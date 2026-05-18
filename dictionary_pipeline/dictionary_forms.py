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

    FULL_STATIVE = "FullStative"
    """A true stative verb. Immediate is given as future progressive. Infinitive is blank."""


PREDICTION_IS_STATIVE: dict[Prediction, bool] = {
    Prediction.FULL_EVENTFUL: False,
    Prediction.FULL_STATIVE: True,
}


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
FORM_NAME_TO_ASPECT_FOR_PREDICTION: dict[Prediction, dict[str, Aspect]] = {
    Prediction.FULL_EVENTFUL: {
        "present": Aspect.PRESENT,
        "present_1sg": Aspect.PRESENT,
        "imperfective": Aspect.IMPERFECTIVE,
        "perfective": Aspect.PERFECTIVE,
        "imperative": Aspect.IMPERATIVE,
        "infinitive": Aspect.INFINITIVE,
    },
    Prediction.FULL_STATIVE: {
        "present": Aspect.PRESENT,
        "present_1sg": Aspect.PRESENT,
        "imperfective": Aspect.IMPERFECTIVE,
        "perfective": Aspect.IMPERFECTIVE,
        "imperative": Aspect.IMPERFECTIVE,
    },
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
    ],
    Prediction.FULL_STATIVE: [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
    ],
}

# All dictionary form columns (for iterating over dictionary rows)
ALL_FORM_NAMES = FORM_NAMES_FOR_PREDICTION[Prediction.FULL_EVENTFUL]


def get_form_spec(prediction: Prediction, form_name: str) -> FormSpec:
    """
    Bridge function: converts a dictionary form_name into a FormSpec.
    Currently hardcoded for Scope.EVENTFUL as per Phase 1 plan.
    """
    person = FORM_NAME_TO_PERSON.get(form_name, Person.THIRD)
    aspect = FORM_NAME_TO_ASPECT_FOR_PREDICTION[prediction].get(
        form_name, Aspect.PRESENT
    )

    # Maintain current behavior: PERFECTIVE and INFINITIVE force Set B
    allow_set_a = aspect not in (Aspect.PERFECTIVE, Aspect.INFINITIVE)

    # Predict tense ending morphologically inside the function!
    if form_name == "imperative" and prediction == Prediction.FULL_STATIVE:
        tense_ending = "ehsti"
    elif form_name == "imperfective":
        tense_ending = "o'i"
    elif form_name == "perfective":
        tense_ending = "v'i"
    elif form_name == "infinitive":
        tense_ending = "i"
    elif form_name in ("present", "present_1sg"):
        tense_ending = "i,a"
    else:
        tense_ending = ""

    return FormSpec(
        name=form_name,
        aspect=aspect,
        person=person,
        allow_set_a=allow_set_a,
        stative=PREDICTION_IS_STATIVE[prediction],
        tense_ending=tense_ending,
    )


def build_wordspec(
    prediction: Prediction, config: PronominalConfig, form_name: str
) -> WordSpec:
    """
    Bridge function: converts a dictionary form_name into a WordSpec.
    """
    # form_spec = get_form_spec(prediction, form_name)
    # Enrich with stative info from the verb
    # form_spec = FormSpec(
    #     aspect=form_spec.aspect,
    #     person=form_spec.person,
    #     allow_set_a=form_spec.allow_set_a,
    #     stative=stative,
    # )

    form_spec = get_form_spec(prediction, form_name)
    return _build_wordspec(form_spec, config)


def _build_wordspec(form_spec: FormSpec, config: PronominalConfig) -> WordSpec:
    """
    Bridge function: converts a dictionary form_name into a WordSpec.
    """
    # form_spec = get_form_spec(prediction, form_name)
    # Enrich with stative info from the verb
    # form_spec = FormSpec(
    #     aspect=form_spec.aspect,
    #     person=form_spec.person,
    #     allow_set_a=form_spec.allow_set_a,
    #     stative=stative,
    # )

    key = calculate_pronominal_key(
        form_spec.aspect, form_spec.person, config, form_spec.stative
    )

    if not key:
        logging.getLogger(__name__).warning(
            f"No Pronominal Key resolvable for {form_spec.name}. Falling back to 3rd Set A"
        )
        person, number, p_set = Person.THIRD, Number.SINGULAR, PronominalSet.SET_A
    else:
        person, number, p_set = key

    return WordSpec(
        aspect=form_spec.aspect,
        stative=form_spec.stative,
        person=person,
        number=number,
        pronominal_set=p_set,
        tense_ending=form_spec.tense_ending,
    )


class TenseEnding(str, Enum):
    I = "i"
    A = "a"
    OI = "o'i"
    VI = "v'i"
    EHSTI = "ehsti"


# Map each dictionary form name to its possible tense endings.
TENSE_ENDINGS_BY_FORM: dict[str, list[str]] = {
    "present": ["i", "a"],
    "present_1sg": ["i", "a"],
    "imperfective": ["o'i"],
    "perfective": ["v'i"],
    "imperative": [],  # Eventful has none, stative is handled dynamically
    "infinitive": ["i"],
}


def get_tense_endings(form_name: str, prediction: Prediction) -> list[str]:
    """
    Get the list of possible tense endings for a given form name and verb prediction class.
    """
    if form_name == "imperative" and prediction == Prediction.FULL_STATIVE:
        return [TenseEnding.EHSTI.value]
    return TENSE_ENDINGS_BY_FORM.get(form_name, [])


def get_tense_ending(form_name: str, val: str, prediction: Prediction) -> str:
    """
    Given a form name and a surface form value, returns the matched tense ending.
    """
    if not val:
        return ""
    if form_name == "imperative" and prediction == Prediction.FULL_STATIVE:
        if val.endswith("ehsti"):
            return "ehsti"

    endings = TENSE_ENDINGS_BY_FORM.get(form_name, [])
    for ending in endings:
        if val.endswith(ending):
            return ending
    return ""


def strip_tense_ending(
    form_name: str, form_val: str, prediction: Prediction
) -> tuple[str, str]:
    """
    Strips the tense ending from a form value based on the form name and verb prediction class.

    Returns a tuple of (stripped_form_val, stripped_ending).
    If no ending is matched, returns (form_val, "").
    """
    if not form_val:
        return "", ""

    if form_name == "imperative" and prediction == Prediction.FULL_STATIVE:
        if form_val.endswith("ehsti"):
            return form_val[:-5], "ehsti"

    endings = TENSE_ENDINGS_BY_FORM.get(form_name, [])
    for ending in endings:
        if form_val.endswith(ending):
            if ending == "i'a":
                # For "i'a", only strip "a", leaving "i'"
                return form_val[:-1], "a"
            return form_val[: -len(ending)], ending

    return form_val, ""


def attach_tense_ending(
    form_name: str, form_val: str, prediction: Prediction, original_form_val: str = ""
) -> str:
    """
    Attaches the appropriate tense ending to a form value.
    If original_form_val is provided, we can determine the exact ending (e.g. 'i' vs 'a' for present).
    Otherwise, we use the first available ending.
    """
    if not form_val:
        return ""

    # Check if a tense ending is already attached
    endings = get_tense_endings(form_name, prediction)
    for ending in endings:
        if ending == "i'a":
            if form_val.endswith("i'a") or form_val.endswith("i'"):
                # If it already ends in i'a, or ends in i' (which is the stripped state of i'a)
                # and we want to attach, if it ends in i' we append 'a'
                if form_val.endswith("i'"):
                    return form_val + "a"
                return form_val
        elif form_val.endswith(ending):
            return form_val

    # Determine the ending to attach
    ending_to_attach = ""
    if original_form_val:
        ending_to_attach = get_tense_ending(form_name, original_form_val, prediction)

    if not ending_to_attach and endings:
        # Fallback to the first ending in the list
        # For present/present_1sg, default to "a"
        if form_name in ("present", "present_1sg"):
            ending_to_attach = "a"
        else:
            ending_to_attach = endings[0]

    return form_val + ending_to_attach
