import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from morphology.metathesis import demetathesize_h, metathesize_h
from morphology.morphemes.middle_voice import MiddleVoice
from morphology.morphology_types import Number, Person, PronominalSet


class StemType(Enum):
    CONSONANT = "con"
    GLOTTAL = "glottal"
    LONG_START = "long"
    VOWEL_A = "vowel_a"
    VOWEL_E = "vowel_e"
    VOWEL_O = "vowel_o"
    VOWEL_U = "vowel_u"
    VOWEL_V = "vowel_v"
    ASPIRATED = "aspirated"  # th-
    S_STEM = "s_stem"  # s-

    def is_valid_for_stem(self, stem: str) -> bool:
        if stem == "":
            # we can't know the suffix used here
            return True
        if self == StemType.ASPIRATED:
            # begins with consonant sequence then h
            return bool(re.match("^[^aeiouvhs]+h", stem))
        elif self == StemType.CONSONANT:
            return bool(re.match("^[^aeiouvs']", stem))
        elif self == StemType.LONG_START:
            return stem.startswith(":")
        elif self == StemType.S_STEM:
            return stem.startswith("hs")
        elif self == StemType.GLOTTAL:
            return stem.startswith("'")
        elif self == StemType.VOWEL_A:
            return stem.startswith("a")
        elif self == StemType.VOWEL_E:
            return stem.startswith("e")
        elif self == StemType.VOWEL_O:
            return stem.startswith("o")
        elif self == StemType.VOWEL_U:
            return stem.startswith("u")
        elif self == StemType.VOWEL_V:
            return stem.startswith("v")
        else:
            raise Exception("Unreachable")


class StemModification(Enum):
    NONE = "none"
    A_REPLACE = "a_replace"
    V_REPLACE = "v_replace"
    GLOTTAL_DROP = "glottal_drop"
    LONG = "long"


@dataclass(frozen=True)
class PronominalConfig:
    set_type: PronominalSet  # SET_A or SET_B
    stem_type: StemType
    allow_h_metathesis: bool = False
    middle_voice: MiddleVoice = MiddleVoice.NONE
    middle_voice_h_metathesis: bool = False

    # Flags for prefix variants
    plural_pronouns: bool = False
    use_ka_variant: bool = False  # 3rd Set A: ka-/k- (True) vs a-/ø (False)
    use_aki_for_1st_set_b: bool = (
        False  # 1st Set B: aki- vs ak- (on consonants, does stem type predict?)
    )
    uwa_replaces_v: bool = False  # Does uwa- replace v-?

    # Functional Flags
    use_3rd_person_object: bool = False  # Use 1->3 and 2->3 forms (imp_type='to_3rd')

    @staticmethod
    def from_row(row: dict[str, str]) -> "PronominalConfig":
        set_type_str = row["set_a_b"].lower()
        set_type = (
            PronominalSet.SET_A
            if set_type_str in ["a", "set a"]
            else PronominalSet.SET_B
        )
        return PronominalConfig(
            set_type=set_type,
            stem_type=StemType(row["stem_type"]),
            allow_h_metathesis=row["allow_h_metathesis"] == "True",
            middle_voice=MiddleVoice(row["middle_voice"]),
            middle_voice_h_metathesis=row["middle_voice_h_metathesis"] == "True",
            plural_pronouns=row["plural"] == "True",
            use_ka_variant=row["ka_variant"] == "True",
            use_aki_for_1st_set_b=row["aki_1st"] == "True",
            uwa_replaces_v=row["uwa_v"] == "True",
            use_3rd_person_object=row["3rd_person_object"] == "True",
        )

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "PronominalConfig":
        # Handle Enums
        clean_data = data.copy()
        if "stem_type" in clean_data and isinstance(clean_data["stem_type"], str):
            clean_data["stem_type"] = StemType(clean_data["stem_type"])
        if "middle_voice" in clean_data and isinstance(clean_data["middle_voice"], str):
            clean_data["middle_voice"] = MiddleVoice(clean_data["middle_voice"])
        if "set_type" in clean_data and isinstance(clean_data["set_type"], str):
            set_type_str = clean_data["set_type"].lower()
            clean_data["set_type"] = (
                PronominalSet.SET_A
                if set_type_str in ["a", "set a"]
                else PronominalSet.SET_B
            )
        return PronominalConfig(**clean_data)

    def to_row(self) -> dict[str, str]:
        row = {}

        row["set_a_b"] = self.set_type.value
        row["stem_type"] = self.stem_type.value
        row["allow_h_metathesis"] = str(self.allow_h_metathesis)
        row["middle_voice"] = self.middle_voice.value
        row["middle_voice_h_metathesis"] = str(self.middle_voice_h_metathesis)
        row["plural"] = str(self.plural_pronouns)
        row["ka_variant"] = str(self.use_ka_variant)
        row["aki_1st"] = str(self.use_aki_for_1st_set_b)
        row["uwa_v"] = str(self.uwa_replaces_v)
        row["3rd_person_object"] = str(self.use_3rd_person_object)

        return row

    @classmethod
    def get_row_keys(cls) -> list[str]:
        return [
            "set_a_b",
            "stem_type",
            "allow_h_metathesis",
            "middle_voice",
            "middle_voice_h_metathesis",
            "plural",
            "ka_variant",
            "aki_1st",
            "uwa_v",
            "3rd_person_object",
        ]


@dataclass
class ConfiguredPrefix:
    form: str
    stem_modification: StemModification = StemModification.NONE
    allow_h_metathesis: bool = False

    def attach(self, stem: str, allow_h_metathesis: bool) -> str:
        if self.allow_h_metathesis and allow_h_metathesis:
            form, stem = metathesize_h(self.form, stem)
        else:
            form, stem = self.form, stem

        if self.stem_modification in [
            StemModification.A_REPLACE,
            StemModification.V_REPLACE,
            StemModification.GLOTTAL_DROP,
        ]:
            # drop first letter
            return form + "->" + stem

        return form + "-" + stem

    def detach(self, word: str, allow_h_metathesis: bool) -> str | None:
        if self.allow_h_metathesis and allow_h_metathesis:
            return demetathesize_h(self.form, word)

        if not word.startswith(self.form):
            return None

        remainder = word[len(self.form) :]
        stem = remainder

        # Reverse Stem Transformations
        if self.stem_modification == StemModification.A_REPLACE:
            stem = "a" + remainder
        elif self.stem_modification == StemModification.GLOTTAL_DROP:
            stem = "'" + remainder
        elif self.stem_modification == StemModification.LONG:
            stem = ":" + remainder
        elif self.stem_modification == StemModification.V_REPLACE:
            stem = "v" + remainder

        return stem


def get_prefix_details(
    key: tuple[Person, Number, PronominalSet], config: PronominalConfig
) -> ConfiguredPrefix:
    res = _get_prefix_details(key, config)
    if isinstance(res, PrefixForms):
        return res.select(config.stem_type)
    elif isinstance(res, ConfiguredPrefix):
        return res
    else:
        raise Exception("Failed to get prefix details", key, config)


@dataclass
class PrefixForms:
    consonant: ConfiguredPrefix
    vowel: ConfiguredPrefix
    vowel_overrides: dict[str, ConfiguredPrefix] = field(default_factory=dict)
    aspirated: ConfiguredPrefix | None = None
    s: ConfiguredPrefix | None = None
    glottal: ConfiguredPrefix | None = None
    long_start: ConfiguredPrefix | None = None

    def select(self, stem: StemType) -> ConfiguredPrefix:
        if stem == StemType.ASPIRATED:
            return self.aspirated if self.aspirated is not None else self.consonant
        elif stem == StemType.S_STEM:
            return self.s if self.s is not None else self.consonant
        elif stem == StemType.GLOTTAL:
            return self.glottal if self.glottal is not None else self.consonant
        elif stem == StemType.LONG_START:
            pron = self.long_start if self.long_start is not None else self.consonant
            # FORCE DEFAULT
            return ConfiguredPrefix(
                form=pron.form, stem_modification=StemModification.LONG
            )
        elif stem == StemType.CONSONANT:
            return self.consonant

        # vowel stuff
        vowel = stem.value.split("_")[1]

        if vowel in self.vowel_overrides:
            return self.vowel_overrides[vowel]
        else:
            return self.vowel


def _get_prefix_details(
    key: tuple[Person, Number, PronominalSet], config: PronominalConfig
) -> PrefixForms | ConfiguredPrefix | None:
    person, number, p_set = key

    if p_set == PronominalSet.SET_B:
        if person == Person.FIRST:
            if number == Number.PLURAL:
                return PrefixForms(
                    consonant=(ConfiguredPrefix("oki")),
                    glottal=ConfiguredPrefix(
                        "oki", stem_modification=StemModification.GLOTTAL_DROP
                    ),
                    vowel=ConfiguredPrefix("og"),
                )
            else:
                return PrefixForms(
                    aspirated=ConfiguredPrefix("akh", allow_h_metathesis=True),
                    s=ConfiguredPrefix("akh", allow_h_metathesis=True),
                    consonant=(
                        ConfiguredPrefix("aki", allow_h_metathesis=True)
                        if config.use_aki_for_1st_set_b
                        else ConfiguredPrefix("ak", allow_h_metathesis=True)
                    ),
                    vowel=ConfiguredPrefix("akw", allow_h_metathesis=True),
                )
        if person == Person.SECOND:
            if number == Number.PLURAL:
                return PrefixForms(
                    consonant=ConfiguredPrefix("itsi"),
                    glottal=ConfiguredPrefix(
                        "itsi", stem_modification=StemModification.GLOTTAL_DROP
                    ),
                    vowel=ConfiguredPrefix("its"),
                )
            else:
                return PrefixForms(
                    aspirated=ConfiguredPrefix("ts", allow_h_metathesis=True),
                    s=ConfiguredPrefix("t", allow_h_metathesis=True),
                    consonant=ConfiguredPrefix("tsa", allow_h_metathesis=True),
                    vowel=ConfiguredPrefix("ts", allow_h_metathesis=True),
                )
        if person == Person.THIRD:
            if number == Number.PLURAL:
                return PrefixForms(
                    consonant=ConfiguredPrefix("uni"),
                    glottal=ConfiguredPrefix(
                        "uni", stem_modification=StemModification.GLOTTAL_DROP
                    ),
                    vowel=ConfiguredPrefix("un"),
                )
            else:
                return PrefixForms(
                    consonant=ConfiguredPrefix("u"),
                    long_start=ConfiguredPrefix("uwa"),
                    glottal=ConfiguredPrefix(
                        "u", stem_modification=StemModification.GLOTTAL_DROP
                    ),
                    vowel=ConfiguredPrefix("uw", allow_h_metathesis=True),
                    vowel_overrides={
                        "a": ConfiguredPrefix("u", StemModification.A_REPLACE),
                        "v": (
                            ConfiguredPrefix("uwa", StemModification.V_REPLACE)
                            if config.uwa_replaces_v
                            else ConfiguredPrefix("uw")
                        ),
                    },
                )

    if p_set == PronominalSet.SET_A:
        if person == Person.FIRST:
            if number == Number.PLURAL:
                return PrefixForms(
                    consonant=ConfiguredPrefix("otsi"),
                    glottal=ConfiguredPrefix(
                        "otsi", stem_modification=StemModification.GLOTTAL_DROP
                    ),
                    vowel=ConfiguredPrefix("ots"),
                )
            else:
                return PrefixForms(
                    consonant=ConfiguredPrefix("tsi"), vowel=ConfiguredPrefix("k")
                )
        if person == Person.SECOND:
            if number == Number.PLURAL:
                return PrefixForms(
                    consonant=ConfiguredPrefix("itsi"),
                    glottal=ConfiguredPrefix(
                        "itsi", stem_modification=StemModification.GLOTTAL_DROP
                    ),
                    vowel=ConfiguredPrefix("its"),
                )
            else:
                return PrefixForms(
                    consonant=ConfiguredPrefix("hi"), vowel=ConfiguredPrefix("h")
                )
        if person == Person.THIRD:
            if number == Number.PLURAL:
                return PrefixForms(
                    consonant=ConfiguredPrefix("ani"),
                    glottal=ConfiguredPrefix(
                        "ani", stem_modification=StemModification.GLOTTAL_DROP
                    ),
                    vowel=ConfiguredPrefix("an"),
                )
            else:
                if config.use_ka_variant:
                    return PrefixForms(
                        consonant=ConfiguredPrefix("ka", allow_h_metathesis=True),
                        vowel=ConfiguredPrefix("k", allow_h_metathesis=True),
                    )
                return PrefixForms(
                    consonant=ConfiguredPrefix("a"),
                    vowel=ConfiguredPrefix(""),
                    vowel_overrides={
                        "a": ConfiguredPrefix("a", StemModification.A_REPLACE)
                    },
                )

    if p_set == PronominalSet.PERSON_TO_PERSON:
        if person == Person.FIRST_TO_THIRD:
            return PrefixForms(
                consonant=ConfiguredPrefix("tsi"),
                long_start=ConfiguredPrefix("tsiya"),
                glottal=ConfiguredPrefix(
                    "tsi", stem_modification=StemModification.GLOTTAL_DROP
                ),
                vowel=ConfiguredPrefix("tsiy"),
            )
        if person == Person.SECOND_TO_THIRD:
            return PrefixForms(
                consonant=ConfiguredPrefix("hi"),
                long_start=ConfiguredPrefix("hiya"),
                glottal=ConfiguredPrefix(
                    "hi", stem_modification=StemModification.GLOTTAL_DROP
                ),
                vowel=ConfiguredPrefix("hiy"),
            )

    return None


def detach_prefix(
    word: str, key: tuple[Person, Number, PronominalSet], config: PronominalConfig
) -> tuple[str | None, bool]:
    prefix = get_prefix_details(key, config)

    stem = prefix.detach(word, config.allow_h_metathesis)

    # Check if metathesis was actually involved
    metathesis_used = prefix.allow_h_metathesis and config.allow_h_metathesis

    return stem, metathesis_used


def use_glottal_grade(person: Person, number: Number, p_set: PronominalSet) -> bool:
    if p_set == PronominalSet.PERSON_TO_PERSON:
        return True
    if (
        p_set == PronominalSet.SET_A
        and person == Person.FIRST
        and number == Number.SINGULAR
    ):
        return True
    return False
