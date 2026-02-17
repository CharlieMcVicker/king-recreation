import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

from king_recreation.metathesis import demetathesize_h, metathesize_h
from king_recreation.morphemes.middle_voice import MiddleVoice


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
            # begins with consonant sequence then s
            return re.match("^[^aeiouvhs]+h", stem)
        elif self == StemType.CONSONANT:
            return re.match("^[^aeiouvs']", stem)
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
    set_type: str  # 'a' or 'b'
    stem_type: StemType
    allow_h_metathesis: bool = False
    middle_voice: MiddleVoice = MiddleVoice.NONE

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
    def from_row(row: dict[str, str]):
        return PronominalConfig(
            set_type=row["set_a_b"],
            stem_type=StemType(row["stem_type"]),
            allow_h_metathesis=row["allow_h_metathesis"] == "True",
            middle_voice=MiddleVoice(row["middle_voice"]),
            plural_pronouns=row["plural"] == "True",
            use_ka_variant=row["ka_variant"] == "True",
            use_aki_for_1st_set_b=row["aki_1st"] == "True",
            uwa_replaces_v=row["uwa_v"] == "True",
            use_3rd_person_object=row["3rd_person_object"] == "True",
        )

    @staticmethod
    def from_dict(data: dict) -> "PronominalConfig":
        # Handle Enums
        clean_data = data.copy()
        if "stem_type" in clean_data and isinstance(clean_data["stem_type"], str):
            clean_data["stem_type"] = StemType(clean_data["stem_type"])
        if "middle_voice" in clean_data and isinstance(clean_data["middle_voice"], str):
            clean_data["middle_voice"] = MiddleVoice(clean_data["middle_voice"])
        return PronominalConfig(**clean_data)

    def to_row(self):
        row = {}

        row["set_a_b"] = self.set_type
        row["stem_type"] = self.stem_type.value
        row["allow_h_metathesis"] = str(self.allow_h_metathesis)
        row["middle_voice"] = self.middle_voice.value
        row["plural"] = str(self.plural_pronouns)
        row["ka_variant"] = str(self.use_ka_variant)
        row["aki_1st"] = str(self.use_aki_for_1st_set_b)
        row["uwa_v"] = str(self.uwa_replaces_v)
        row["3rd_person_object"] = str(self.use_3rd_person_object)

        return row


def get_pronominal_set_name(
    form_name: str, config: PronominalConfig, stative: bool
) -> Optional[str]:
    set_type = config.set_type
    use_3rd_person_object = config.use_3rd_person_object

    set_a = set_type in ["Set A", "a"]

    if form_name == "present" or form_name == "imperfective":
        if config.plural_pronouns:
            return "3pl Set A" if set_a else "3pl Set B"
        else:
            return "3rd Set A" if set_a else "3rd Set B"
    if form_name == "perfective" or form_name == "infinitive":
        if config.plural_pronouns:
            return (
                "3pl Set A"
                if set_a and stative and not form_name == "infinitive"
                else "3pl Set B"
            )
        else:
            return (
                "3rd Set A"
                if set_a and stative and not form_name == "infinitive"
                else "3rd Set B"
            )
    if form_name == "imperative":
        if config.plural_pronouns:
            return "2pl Set A" if set_a else "2pl Set B"
        else:
            return (
                "2nd to 3rd"
                if use_3rd_person_object
                else ("2nd Set A" if set_a else "2nd Set B")
            )
    if form_name == "present_1sg":
        if config.plural_pronouns:
            return "1pl Set A" if set_a else "1pl Set B"
        else:
            return (
                "1st to 3rd"
                if use_3rd_person_object
                else ("1st Set A" if set_a else "1st Set B")
            )
    return None


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

    def detach(self, word: str, allow_h_metathesis: bool) -> Optional[str]:
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


def get_prefix_details(set_name: str, config: PronominalConfig) -> ConfiguredPrefix:
    res = _get_prefix_details(set_name, config)
    if isinstance(res, PrefixForms):
        return res.select(config.stem_type)
    elif isinstance(res, ConfiguredPrefix):
        return res
    else:
        print(set_name)
        raise Exception("Failed to get prefix details", set_name, config)


@dataclass
class PrefixForms:
    consonant: ConfiguredPrefix
    vowel: ConfiguredPrefix
    vowel_overrides: Dict[str, ConfiguredPrefix] = field(default_factory=dict)
    aspirated: Optional[ConfiguredPrefix] = None
    s: Optional[ConfiguredPrefix] = None
    glottal: Optional[ConfiguredPrefix] = None
    long_start: Optional[ConfiguredPrefix] = None

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
    set_name: str, config: PronominalConfig
) -> Tuple[str, StemModification]:
    if set_name == "1st Set B":
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

    if set_name == "1pl Set B":
        return PrefixForms(
            consonant=(ConfiguredPrefix("oki")),
            glottal=ConfiguredPrefix(
                "oki", stem_modification=StemModification.GLOTTAL_DROP
            ),
            vowel=ConfiguredPrefix("og"),
        )

    if set_name == "2nd Set B":
        return PrefixForms(
            aspirated=ConfiguredPrefix("ts", allow_h_metathesis=True),
            s=ConfiguredPrefix("t", allow_h_metathesis=True),
            consonant=ConfiguredPrefix("tsa", allow_h_metathesis=True),
            vowel=ConfiguredPrefix("ts", allow_h_metathesis=True),
        )

    if set_name == "2pl Set B":
        return PrefixForms(
            consonant=ConfiguredPrefix("itsi"),
            glottal=ConfiguredPrefix(
                "itsi", stem_modification=StemModification.GLOTTAL_DROP
            ),
            vowel=ConfiguredPrefix("its"),
        )

    if set_name == "3rd Set B":
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

    if set_name == "3pl Set B":
        return PrefixForms(
            consonant=ConfiguredPrefix("uni"),
            glottal=ConfiguredPrefix(
                "uni", stem_modification=StemModification.GLOTTAL_DROP
            ),
            vowel=ConfiguredPrefix("un"),
        )

    if set_name == "1st Set A":
        return PrefixForms(
            consonant=ConfiguredPrefix("tsi"), vowel=ConfiguredPrefix("k")
        )

    if set_name == "1pl Set A":
        return PrefixForms(
            consonant=ConfiguredPrefix("otsi"),
            glottal=ConfiguredPrefix(
                "otsi", stem_modification=StemModification.GLOTTAL_DROP
            ),
            vowel=ConfiguredPrefix("ots"),
        )

    if set_name == "2nd Set A":
        return PrefixForms(
            consonant=ConfiguredPrefix("hi"), vowel=ConfiguredPrefix("h")
        )

    if set_name == "2pl Set A":
        return PrefixForms(
            consonant=ConfiguredPrefix("itsi"),
            glottal=ConfiguredPrefix(
                "itsi", stem_modification=StemModification.GLOTTAL_DROP
            ),
            vowel=ConfiguredPrefix("its"),
        )

    if set_name == "3rd Set A":
        if config.use_ka_variant:
            return PrefixForms(
                consonant=ConfiguredPrefix("ka", allow_h_metathesis=True),
                vowel=ConfiguredPrefix("k", allow_h_metathesis=True),
            )
        # Some H-stems take k- even if not 'ka-variant' in the traditional sense?
        # No, let's keep it strict. If it works, it works.
        return PrefixForms(
            consonant=ConfiguredPrefix("a"),
            vowel=ConfiguredPrefix(""),
            vowel_overrides={"a": ConfiguredPrefix("a", StemModification.A_REPLACE)},
        )

    if set_name == "3pl Set A":
        return PrefixForms(
            consonant=ConfiguredPrefix("ani"),
            glottal=ConfiguredPrefix(
                "ani", stem_modification=StemModification.GLOTTAL_DROP
            ),
            vowel=ConfiguredPrefix("an"),
        )

    if set_name == "1st to 3rd":
        return PrefixForms(
            consonant=ConfiguredPrefix("tsi"),
            long_start=ConfiguredPrefix("tsiya"),
            glottal=ConfiguredPrefix(
                "tsi", stem_modification=StemModification.GLOTTAL_DROP
            ),
            vowel=ConfiguredPrefix("tsiy"),
        )

    if set_name == "2nd to 3rd":
        return PrefixForms(
            consonant=ConfiguredPrefix("hi"),
            long_start=ConfiguredPrefix("hiya"),
            glottal=ConfiguredPrefix(
                "hi", stem_modification=StemModification.GLOTTAL_DROP
            ),
            vowel=ConfiguredPrefix("hiy"),
        )

    return None


def detach_prefix(word: str, form_name: str, config: PronominalConfig, stative: bool):
    set_name = get_pronominal_set_name(form_name, config, stative)
    prefix = get_prefix_details(set_name, config)

    stem = prefix.detach(word, config.allow_h_metathesis)

    # Check if metathesis was actually involved
    metathesis_used = prefix.allow_h_metathesis and config.allow_h_metathesis

    return stem, metathesis_used


def use_glottal_grade_for_set(set_name: str) -> bool:
    return set_name in ["2nd to 3rd", "1st to 3rd", "1st Set A"]


def use_glottal_grade(form: str, config: PronominalConfig, stative: bool) -> bool:
    return use_glottal_grade_for_set(get_pronominal_set_name(form, config, stative))
