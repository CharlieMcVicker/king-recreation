import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Optional, Tuple

from king_recreation.morphemes.middle_voice import MiddleVoice
from king_recreation.phonology_data import VOWEL_SET


class StemType(Enum):
    CONSONANT = "con"
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
            return re.match("^[^aeiouvs]", stem)
        elif self == StemType.S_STEM:
            return stem.startswith("hs")
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


class MetathesisStrategy(Enum):
    NONE = "none"
    H_CONS = "h_cons"  # kha- / tsha- / akhi-
    VOWEL = "vowel"  # kh- / h- / uhw- / ...


class Condition(Enum):
    VOWEL_AE = "vowel_ae"
    VOWEL = "vowel"
    CONSONANT = "con"
    A_REPLACE = "a_replace"
    V_REPLACE = "v_replace"
    VOWEL_NO_A = "vowel_no_a"
    ASPIRATED = "aspirated"
    S_STEM = "s_stem"
    METATHESIS_H_CONS = "metathesis_h_cons"
    METATHESIS_VOWEL = "metathesis_vowel"


@dataclass(frozen=True)
class PronominalConfig:
    set_type: str  # 'a' or 'b'
    stem_type: StemType
    metathesis_strategy: MetathesisStrategy = MetathesisStrategy.NONE
    middle_voice: MiddleVoice = MiddleVoice.NONE

    # Flags for prefix variants
    plural_pronouns: bool = False
    use_ka_variant: bool = False  # 3rd Set A: ka-/k- (True) vs a-/ø (False)
    long_start: bool = (
        False  # 3rd Set B: uwa- vs u- (on consonants), tsiya- vs tsi- on person-person
    )
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
            metathesis_strategy=MetathesisStrategy(row["metathesis_strategy"]),
            middle_voice=MiddleVoice(row["middle_voice"]),
            plural_pronouns=row["plural"] == "True",
            use_ka_variant=row["ka_variant"] == "True",
            long_start=row["long_start"] == "True",
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
        if "metathesis_strategy" in clean_data and isinstance(
            clean_data["metathesis_strategy"], str
        ):
            clean_data["metathesis_strategy"] = MetathesisStrategy(
                clean_data["metathesis_strategy"]
            )
        if "middle_voice" in clean_data and isinstance(clean_data["middle_voice"], str):
            clean_data["middle_voice"] = MiddleVoice(clean_data["middle_voice"])
        return PronominalConfig(**clean_data)

    def to_row(self):
        row = {}

        row["set_a_b"] = self.set_type
        row["stem_type"] = self.stem_type.value
        row["metathesis_strategy"] = self.metathesis_strategy.value
        row["middle_voice"] = self.middle_voice.value
        row["plural"] = str(self.plural_pronouns)
        row["ka_variant"] = str(self.use_ka_variant)
        row["long_start"] = str(self.long_start)
        row["aki_1st"] = str(self.use_aki_for_1st_set_b)
        row["uwa_v"] = str(self.uwa_replaces_v)
        row["3rd_person_object"] = str(self.use_3rd_person_object)

        return row


def get_pronominal_set_name(form_name: str, config: PronominalConfig) -> Optional[str]:
    set_type = config.set_type
    use_3rd_person_object = config.use_3rd_person_object

    if form_name == "present" or form_name == "imperfective":
        if config.plural_pronouns:
            return "3pl Set A" if set_type in ["Set A", "a"] else "3pl Set B"
        else:
            return "3rd Set A" if set_type in ["Set A", "a"] else "3rd Set B"
    if form_name == "perfective" or form_name == "infinitive":
        if config.plural_pronouns:
            return "3pl Set B"
        else:
            return "3rd Set B"
    if form_name == "imperative":
        if config.plural_pronouns:
            return "2pl Set A" if set_type in ["Set A", "a"] else "2pl Set B"
        else:
            return (
                "2nd to 3rd"
                if use_3rd_person_object
                else ("2nd Set A" if set_type in ["Set A", "a"] else "2nd Set B")
            )
    if form_name == "present_1sg":
        if config.plural_pronouns:
            return "1pl Set A" if set_type in ["Set A", "a"] else "1pl Set B"
        else:
            return (
                "1st to 3rd"
                if use_3rd_person_object
                else ("1st Set A" if set_type in ["Set A", "a"] else "1st Set B")
            )
    return None


@dataclass
class PartlyConfiguredPrefix:
    form: str
    condition: Optional[Condition] = None

    def configure(self, stem: StemType):
        if self.condition:
            return ConfiguredPrefix(self.form, self.condition)
        elif stem == StemType.ASPIRATED:
            return ConfiguredPrefix(self.form, Condition.ASPIRATED)
        elif stem == StemType.CONSONANT:
            return ConfiguredPrefix(self.form, Condition.CONSONANT)
        elif stem == StemType.S_STEM:
            return ConfiguredPrefix(self.form, Condition.S_STEM)
        elif stem == StemType.VOWEL_A:
            return ConfiguredPrefix(self.form, Condition.VOWEL_AE)
        elif stem == StemType.VOWEL_E:
            return ConfiguredPrefix(self.form, Condition.VOWEL_AE)
        return ConfiguredPrefix(self.form, Condition.VOWEL_NO_A)


@dataclass
class ConfiguredPrefix:
    form: str
    condition: Condition

    def attach(self, stem: str) -> str:
        if self.condition == Condition.METATHESIS_H_CONS:
            if stem[0] in VOWEL_SET:
                # ka + ah... -> khah...
                return self.form[:-1] + "h" + stem[0] + stem[2:]
            else:
                # ka + n... -> kan... -> khan... (aspiration moves to prefix)
                return self.form[:-1] + "h" + self.form[-1:] + stem[0] + stem[2:]

        if self.condition == Condition.METATHESIS_VOWEL:
            if len(stem) > 1 and stem[1] == "h":
                # u- + ah... -> uhw...
                if self.form == "u":
                    # Check for double w formation from stem starting with w
                    # e.g., u- + ahw... -> uwhw... (simplified to uwh...)
                    res = "uwh" + stem[2:]
                    if res.startswith("uwhw"):
                        return "uwh" + res[4:]
                    return res
                return self.form + stem[0] + stem[2:]

        if self.condition == Condition.A_REPLACE:
            if stem.startswith("a"):
                return self.form + stem[1:]
        if self.condition == Condition.V_REPLACE:
            if stem.startswith("v"):
                return self.form + stem[1:]

        return self.form + stem

    def detach(
        self,
        word: str,
    ) -> Optional[str]:
        if self.condition == Condition.METATHESIS_H_CONS:
            # Match 'kha' for 'ka'
            meta_pref = self.form[:-1] + "h" + self.form[-1:]
            if word.startswith(meta_pref):
                remainder = word[len(meta_pref) :]
                return remainder[0] + "h" + remainder[1:]

        # Heuristic for ka+h -> kh merger (for non-metathesis or implicit metathesis)
        # Only applies if the 'a' is missing (syncopated), e.g. khtosadi.
        # If word is kha..., we should let standard logic or METATHESIS_H_CONS handle it.
        form = self.form
        if self.form == "ka" and word.startswith("kh") and not word.startswith("kha"):
            form = "k"

        if not word.startswith(form):
            return None

        remainder = word[len(form) :]
        stem = remainder

        if self.condition == Condition.METATHESIS_VOWEL:
            if form == "u" and word.startswith("uwh"):
                remainder = word[3:]
                # If remainder starts with a vowel, w was likely part of the stem (ahw...)
                # Preservation of /w/ before vowels (e.g. uhwolates -> ahwolates)
                if remainder and remainder[0] in VOWEL_SET:
                    return "awh" + remainder
                return "ah" + remainder
            if remainder:
                stem = remainder[0:2] + remainder[2:] + "h"

        # Reverse Stem Transformations
        if self.condition == Condition.A_REPLACE:
            stem = "a" + remainder
        elif self.condition == Condition.V_REPLACE:
            stem = "v" + remainder

        # Regressions/Constraints
        if self.condition == Condition.ASPIRATED:
            # Restriction: ak- (akh-) before -i is not valid
            if form == "akh" and stem.startswith("i"):
                return None
            # Restriction: ts- before -ha is not valid
            if form == "ts" and stem.startswith("ha"):
                return None

        return stem


def get_prefix_details(set_name: str, config: PronominalConfig) -> ConfiguredPrefix:
    res = _get_prefix_details(set_name, config)
    if isinstance(res, PrefixForms):
        return res.select(config.stem_type)
    elif res == None:
        print(set_name)
    else:
        form, condition = res
        return ConfiguredPrefix(form, condition)


@dataclass
class PrefixForms:
    consonant: PartlyConfiguredPrefix
    vowel: PartlyConfiguredPrefix
    vowel_overrides: Dict[str, PartlyConfiguredPrefix] = field(default_factory=dict)
    aspirated: Optional[PartlyConfiguredPrefix] = None
    s: Optional[PartlyConfiguredPrefix] = None

    def _select(self, stem: StemType) -> PartlyConfiguredPrefix:
        if stem == StemType.ASPIRATED:
            return self.aspirated if self.aspirated is not None else self.consonant
        elif stem == StemType.S_STEM:
            return self.s if self.s is not None else self.consonant
        elif stem == StemType.CONSONANT:
            return self.consonant

        # vowel stuff
        vowel = stem.value.split("_")[1]

        if vowel in self.vowel_overrides:
            return self.vowel_overrides[vowel]
        else:
            return self.vowel

    def select(self, stem: StemType) -> ConfiguredPrefix:
        s = self._select(stem)
        return s.configure(stem)


def _get_prefix_details(
    set_name: str, config: PronominalConfig
) -> Tuple[str, Condition]:
    s_type = config.stem_type
    meta = config.metathesis_strategy
    is_con = s_type in [StemType.CONSONANT, StemType.ASPIRATED, StemType.S_STEM]

    if meta == MetathesisStrategy.H_CONS:
        if set_name == "3rd Set A" and config.use_ka_variant:
            return "ka", Condition.METATHESIS_H_CONS
        if set_name == "2nd Set B":
            return "tsa", Condition.METATHESIS_H_CONS
        if set_name == "1st Set B":
            return "aki", Condition.METATHESIS_H_CONS

    if meta == MetathesisStrategy.VOWEL:
        if set_name == "3rd Set A":
            return "kh", Condition.METATHESIS_VOWEL
        # B-set vowels for VOWEL meta
        if set_name == "3rd Set B":
            return (
                ("u", Condition.METATHESIS_VOWEL)
                if s_type == StemType.VOWEL_A
                # Use 'uwh-' for vowel metathesis to match the new respelling reform (wh, yh, lh, nh)
                # where 'h' follows the resonant.
                else ("uwh", Condition.METATHESIS_VOWEL)
            )

    if set_name == "1st Set B":
        return PrefixForms(
            aspirated=PartlyConfiguredPrefix("akh"),
            s=PartlyConfiguredPrefix("akh"),
            consonant=(
                PartlyConfiguredPrefix("aki")
                if config.use_aki_for_1st_set_b
                else PartlyConfiguredPrefix("ak")
            ),
            vowel=PartlyConfiguredPrefix("akw"),
        )

    if set_name == "1pl Set B":
        return PrefixForms(
            consonant=(PartlyConfiguredPrefix("oki")),
            vowel=PartlyConfiguredPrefix("og"),
        )

    if set_name == "2nd Set B":
        return PrefixForms(
            aspirated=PartlyConfiguredPrefix(
                "ts",
            ),
            s=PartlyConfiguredPrefix(
                "t",
            ),
            consonant=PartlyConfiguredPrefix(
                "tsa",
            ),
            vowel=PartlyConfiguredPrefix("ts"),
        )

    if set_name == "2pl Set B":
        return PrefixForms(
            consonant=(PartlyConfiguredPrefix("itsi")),
            vowel=PartlyConfiguredPrefix("its"),
        )

    if set_name == "3rd Set B":
        return PrefixForms(
            consonant=(
                PartlyConfiguredPrefix("uwa", Condition.CONSONANT)
                if config.long_start
                else PartlyConfiguredPrefix("u", Condition.CONSONANT)
            ),
            vowel=PartlyConfiguredPrefix("uw"),
            vowel_overrides={
                "a": PartlyConfiguredPrefix("u", Condition.A_REPLACE),
                "v": (
                    PartlyConfiguredPrefix("uwa", Condition.V_REPLACE)
                    if config.uwa_replaces_v
                    else PartlyConfiguredPrefix("uw", Condition.VOWEL_NO_A)
                ),
            },
        )

    if set_name == "3pl Set B":
        return PrefixForms(
            consonant=PartlyConfiguredPrefix("uni"),
            vowel=PartlyConfiguredPrefix("un"),
        )

    if set_name == "1st Set A":
        return PrefixForms(
            consonant=PartlyConfiguredPrefix("tsi"), vowel=PartlyConfiguredPrefix("k")
        )

    if set_name == "1pl Set A":
        return PrefixForms(
            consonant=PartlyConfiguredPrefix("otsi"),
            vowel=PartlyConfiguredPrefix("ots"),
        )

    if set_name == "2nd Set A":
        return PrefixForms(
            consonant=PartlyConfiguredPrefix("hi"), vowel=PartlyConfiguredPrefix("h")
        )

    if set_name == "2pl Set A":
        return PrefixForms(
            consonant=PartlyConfiguredPrefix("itsi"),
            vowel=PartlyConfiguredPrefix("its"),
        )

    if set_name == "3rd Set A":
        if config.use_ka_variant:
            return PrefixForms(
                consonant=PartlyConfiguredPrefix("ka"),
                vowel=PartlyConfiguredPrefix("k"),
            )
        # Some H-stems take k- even if not 'ka-variant' in the traditional sense?
        # No, let's keep it strict. If it works, it works.
        return PrefixForms(
            consonant=PartlyConfiguredPrefix("a"),
            vowel=PartlyConfiguredPrefix(""),
        )

    if set_name == "3pl Set A":
        return PrefixForms(
            consonant=PartlyConfiguredPrefix("ani"),
            vowel=PartlyConfiguredPrefix("an"),
        )

    if set_name == "1st to 3rd":
        return PrefixForms(
            consonant=(
                PartlyConfiguredPrefix("tsiya")
                if config.long_start
                else PartlyConfiguredPrefix("tsi")
            ),
            vowel=PartlyConfiguredPrefix("tsiy"),
        )

    if set_name == "2nd to 3rd":
        return PrefixForms(
            consonant=(
                PartlyConfiguredPrefix("hiya")
                if config.long_start
                else PartlyConfiguredPrefix("hi")
            ),
            vowel=PartlyConfiguredPrefix("hiy"),
        )

    return None


def detach_prefix(word: str, form_name: str, config: PronominalConfig):
    set_name = get_pronominal_set_name(form_name, config)
    prefix = get_prefix_details(set_name, config)

    stem = prefix.detach(word)

    metathesis_used = False

    # Check if metathesis was actually involved
    if prefix.condition in [Condition.METATHESIS_H_CONS, Condition.METATHESIS_VOWEL]:
        metathesis_used = True

    # why two checks.. bad TODO: fix
    if prefix.form == "ka" and word.startswith("kh"):
        metathesis_used = True

    return stem, metathesis_used


def use_glottal_grade_for_set(set_name: str) -> bool:
    return set_name in ["2nd to 3rd", "1st to 3rd", "1st Set A"]


def use_glottal_grade(form: str, config: PronominalConfig) -> bool:
    return use_glottal_grade_for_set(get_pronominal_set_name(form, config))
