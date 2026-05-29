"""
Bridge between dictionary column schemas and the morphological WordSpec system.

This module owns the mapping from dictionary form names (column headers like
"present", "present_1sg") to morphological concepts (Aspect, person).

Dictionary-pipeline modules should import from here.
Morphological-core modules should import from word_spec directly.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable

from morphology.morphemes.prefixes.pronominals import PronominalConfig
from morphology.reconstruction import MorphologicalVerb
from morphology.word_spec import Aspect, Number, Person, PronominalSet, WordSpec


@dataclass(frozen=True)
class FormSpec:
    name: str
    aspect: Aspect
    person: Person
    allow_set_a: bool
    stative: bool
    tense_ending: str = ""


@dataclass
class VerbMeta:
    corpus_id: str
    definition: str
    entry_no: str

    @classmethod
    def get_row_keys(cls) -> list[str]:
        return ["corpus_id", "entry_no", "definition"]

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "VerbMeta":
        return cls(
            corpus_id=row.get("corpus_id", ""),
            definition=row.get("definition", ""),
            entry_no=row["entry_no"],
        )


@dataclass(kw_only=True)
class PredictionMeta(VerbMeta):
    prediction: "Prediction"

    @classmethod
    def get_row_keys(cls) -> list[str]:
        return super().get_row_keys() + ["prediction"]

    @classmethod
    def from_row(cls, row: dict[str, str]) -> "PredictionMeta":
        return cls(
            corpus_id=row.get("corpus_id", ""),
            definition=row.get("definition", ""),
            entry_no=row["entry_no"],
            prediction=Prediction(row.get("prediction") or "FullEventful"),
        )


@dataclass
class DictionaryVerb:
    meta: PredictionMeta
    morphology: MorphologicalVerb
    derivations: list["DictionaryVerb"] = field(default_factory=list)
    shim: "DictionaryVerb | None" = None
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
        if "meta" in clean_data:
            if isinstance(clean_data["meta"], dict):
                clean_data["meta"] = PredictionMeta(
                    corpus_id=str(clean_data["meta"].get("corpus_id", "")),
                    definition=str(clean_data["meta"].get("definition", "")),
                    entry_no=str(clean_data["meta"].get("entry_no", "")),
                    prediction=Prediction(
                        clean_data["meta"].get("prediction") or "FullEventful"
                    ),
                )
        else:
            clean_data["meta"] = PredictionMeta(
                corpus_id=str(clean_data.pop("corpus_id", "") or ""),
                definition=str(clean_data.pop("definition", "") or ""),
                entry_no=str(clean_data.pop("entry_no", "") or ""),
                prediction=Prediction(
                    clean_data.pop("prediction", "FullEventful") or "FullEventful"
                ),
            )
        if "morphology" in clean_data:
            clean_data["morphology"] = MorphologicalVerb.from_dict(
                clean_data["morphology"]
            )
        if "derivations" in clean_data:
            clean_data["derivations"] = [
                DictionaryVerb.from_dict(d) for d in clean_data["derivations"]
            ]
        if "shim" in clean_data and clean_data["shim"]:
            clean_data["shim"] = DictionaryVerb.from_dict(clean_data["shim"])
        return DictionaryVerb(**clean_data)

    @property
    def corpus_id(self) -> int | None:
        try:
            return int(self.meta.corpus_id) if self.meta.corpus_id else None
        except ValueError:
            return None

    @corpus_id.setter
    def corpus_id(self, val: Any) -> None:
        self.meta.corpus_id = str(val) if val is not None else ""

    @property
    def entry_no(self) -> int | None:
        try:
            return int(self.meta.entry_no) if self.meta.entry_no else None
        except ValueError:
            return None

    @entry_no.setter
    def entry_no(self, val: Any) -> None:
        self.meta.entry_no = str(val) if val is not None else ""

    @property
    def definition(self) -> str:
        return self.meta.definition

    @definition.setter
    def definition(self, val: str) -> None:
        self.meta.definition = val

    @property
    def prediction(self) -> "Prediction":
        return self.meta.prediction

    @prediction.setter
    def prediction(self, val: "Prediction") -> None:
        self.meta.prediction = val


class Prediction(str, Enum):
    """
    Enum saying which fields of a verb are being modeled in a given
    derivation
    """

    FULL_EVENTFUL = "FullEventful"
    """Attempts to predice all forms for a standard five-aspect verb"""

    FULL_STATIVE = "FullStative"
    """A true stative verb. Immediate is given as future progressive. Infinitive is blank."""

    INF_EVENTFUL = "InfEventful"
    """A prediction made for _only_ the infinitive form of a verb. Used together
    with a FULL_STATIVE to predict all forms of a row"""


@dataclass
class RowPredictionsSpec:
    """
    Captures how a row is predicted by a span of Predictions
    (eg. FullStative + InfEventful)
    """

    name: str
    row_test: Callable[[dict[str, str]], bool]
    predictions: list[tuple[Prediction, Callable[[dict[str, str]], bool]]]


form_exists = lambda form: lambda forms: bool(forms[form])

ROW_PREDICTION_SPECS = [
    RowPredictionsSpec(
        name="FullEventful",
        row_test=lambda _: True,
        predictions=[(Prediction.FULL_EVENTFUL, lambda _: True)],
    ),
    RowPredictionsSpec(
        name="FullStative",
        row_test=lambda forms: not forms["imperative"]
        or forms["imperative"].endswith("ehsti"),
        predictions=[
            (
                Prediction.FULL_STATIVE,
                lambda _: True,
            ),
            (Prediction.INF_EVENTFUL, form_exists("infinitive")),
        ],
    ),
]

PREDICTION_IS_STATIVE: dict[Prediction, bool] = {
    Prediction.FULL_EVENTFUL: False,
    Prediction.FULL_STATIVE: True,
    Prediction.INF_EVENTFUL: False,
}

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
    Prediction.INF_EVENTFUL: {
        "infinitive": Aspect.INFINITIVE,
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
    Prediction.INF_EVENTFUL: [
        "infinitive",
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


def calculate_pronominal_key(
    form_spec: FormSpec, config: PronominalConfig
) -> tuple[Person, Number, PronominalSet] | None:
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
    target_set_is_a = is_set_a and form_spec.allow_set_a

    target_set = PronominalSet.SET_A if target_set_is_a else PronominalSet.SET_B

    if form_spec.person == Person.FIRST:
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
    elif form_spec.person == Person.SECOND:
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

    elif form_spec.person == Person.THIRD:
        if plural:
            return (Person.THIRD, Number.PLURAL, target_set)
        else:
            return (Person.THIRD, Number.SINGULAR, target_set)

    # # Fallback for unexpected person (e.g. if person was empty but aspect was imperative)
    # TODO: delete
    # if aspect == Aspect.IMPERATIVE:
    #     if plural:
    #         return (Person.SECOND, Number.PLURAL, target_set)
    #     else:
    #         if use_3rd_person_object:
    #             return (
    #                 Person.SECOND_TO_THIRD,
    #                 Number.SINGULAR,
    #                 PronominalSet.PERSON_TO_PERSON,
    #             )
    #         else:
    #             return (Person.SECOND, Number.SINGULAR, target_set)

    return None


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

    key = calculate_pronominal_key(form_spec, config)

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
