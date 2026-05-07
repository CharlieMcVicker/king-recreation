"""
Bridge between dictionary column schemas and the morphological WordSpec system.

This module owns the mapping from dictionary form names (column headers like
"present", "present_1sg") to morphological concepts (Aspect, person).

Dictionary-pipeline modules should import from here.
Morphological-core modules should import from word_spec directly.
"""

import logging

from king_recreation.morphemes.prefixes.pronominals import PronominalConfig
from king_recreation.word_spec import (
    Aspect,
    FormSpec,
    Number,
    Person,
    PronominalSet,
    WordSpec,
    calculate_pronominal_key,
)

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
