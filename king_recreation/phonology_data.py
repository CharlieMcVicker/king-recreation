from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple
import re
from king_recreation.morphemes.middle_voice import MiddleVoice


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
    VOWEL_NO_A = "vowel_no_a"
    V = "v"
    ASPIRATED = "aspirated"
    S_STEM = "s_stem"
    METATHESIS_H_CONS = "metathesis_h_cons"
    METATHESIS_VOWEL = "metathesis_vowel"


@dataclass(frozen=True)
class PrePronominalConfig:
    translocutive: bool = False
    translocutiveImpOnly: bool = False
    partitive: bool = False
    distributive: bool = False
    distributiveImpIsFutProg: bool = False

    @staticmethod
    def from_row(row: dict[str, str]):
        return PrePronominalConfig(
            translocutive=row["translocutive"] == "True",
            translocutiveImpOnly=row["translocutive_imp_only"] == "True",
            partitive=row["partitive"] == "True",
            distributive=row["distributive"] == "True",
            distributiveImpIsFutProg=row["distributive_fut_prog"] == "True",
        )

    @staticmethod
    def from_dict(data: dict) -> "PrePronominalConfig":
        return PrePronominalConfig(**data)

    def to_row(self) -> dict[str, str]:
        row = {}

        row["translocutive"] = str(self.translocutive)
        row["translocutive_imp_only"] = str(self.translocutiveImpOnly)
        row["partitive"] = str(self.partitive)
        row["distributive"] = str(self.distributive)
        row["distributive_fut_prog"] = str(self.distributiveImpIsFutProg)

        return row


@dataclass(frozen=True)
class PronominalConfig:
    set_type: str  # 'a' or 'b'
    stem_type: StemType
    metathesis_strategy: MetathesisStrategy = MetathesisStrategy.NONE
    middle_voice: MiddleVoice = MiddleVoice.NONE

    # Flags for prefix variants
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
        row["ka_variant"] = str(self.use_ka_variant)
        row["long_start"] = str(self.long_start)
        row["aki_1st"] = str(self.use_aki_for_1st_set_b)
        row["uwa_v"] = str(self.uwa_replaces_v)
        row["3rd_person_object"] = str(self.use_3rd_person_object)

        return row


@dataclass(frozen=True)
class VerbConfig:
    pre: PrePronominalConfig
    pron: PronominalConfig

    @staticmethod
    def from_row(stem_row: dict[str, str]) -> "VerbConfig":
        pre_config = PrePronominalConfig.from_row(stem_row)
        pron_config = PronominalConfig.from_row(stem_row)

        return VerbConfig(pre=pre_config, pron=pron_config)

    @staticmethod
    def from_dict(data: dict) -> "VerbConfig":
        return VerbConfig(
            pre=PrePronominalConfig.from_dict(data.get("pre", {})),
            pron=PronominalConfig.from_dict(data.get("pron", {})),
        )


def get_vowel_set():
    return {"a", "e", "o", "u", "v", "i"}


VOWEL_SET = get_vowel_set()


def get_pronominal_set_name(form_name: str, config: PronominalConfig) -> Optional[str]:
    set_type = config.set_type
    use_3rd_person_object = config.use_3rd_person_object

    if form_name == "present" or form_name == "imperfective":
        return "3rd Set A" if set_type in ["Set A", "a"] else "3rd Set B"
    if form_name == "perfective" or form_name == "infinitive":
        return "3rd Set B"
    if form_name == "imperative":
        return (
            "2nd to 3rd"
            if use_3rd_person_object
            else ("2nd Set A" if set_type in ["Set A", "a"] else "2nd Set B")
        )
    if form_name == "present_1sg":
        return (
            "1st to 3rd"
            if use_3rd_person_object
            else ("1st Set A" if set_type in ["Set A", "a"] else "1st Set B")
        )
    return None


def get_prefix_details(
    set_name: str, config: PronominalConfig
) -> Tuple[str, Condition]:
    s_type = config.stem_type
    meta = config.metathesis_strategy
    is_con = s_type in [StemType.CONSONANT, StemType.ASPIRATED, StemType.S_STEM]

    if meta == MetathesisStrategy.H_CONS:
        if set_name == "3rd Set A" and config.use_ka_variant:
            return "ka-", Condition.METATHESIS_H_CONS
        if set_name == "2nd Set B":
            return "tsa-", Condition.METATHESIS_H_CONS
        if set_name == "1st Set B":
            return "aki-", Condition.METATHESIS_H_CONS

    if meta == MetathesisStrategy.VOWEL:
        if set_name == "3rd Set A":
            return "kh-", Condition.METATHESIS_VOWEL
        # B-set vowels for VOWEL meta
        if set_name == "3rd Set B":
            return (
                ("u-", Condition.METATHESIS_VOWEL)
                if s_type == StemType.VOWEL_A
                # Use 'uwh-' for vowel metathesis to match the new respelling reform (wh, yh, lh, nh)
                # where 'h' follows the resonant.
                else ("uwh-", Condition.METATHESIS_VOWEL)
            )
        if set_name == "2nd Set A":
            return "h-", Condition.VOWEL

    if set_name == "3rd Set A":
        if config.use_ka_variant:
            return ("ka-", Condition.CONSONANT) if is_con else ("k-", Condition.VOWEL)
        # Some H-stems take k- even if not 'ka-variant' in the traditional sense?
        # No, let's keep it strict. If it works, it works.
        if is_con:
            return "a-", Condition.CONSONANT
        return "ø", Condition.VOWEL_AE

    if set_name == "3rd Set B":
        if s_type == StemType.VOWEL_A:
            return "u-", Condition.A_REPLACE
        if s_type == StemType.VOWEL_V:
            return (
                ("uwa-", Condition.V)
                if config.uwa_replaces_v
                else ("uw-", Condition.VOWEL_NO_A)
            )
        if s_type in [
            StemType.VOWEL_E,
            StemType.VOWEL_O,
            StemType.VOWEL_U,
        ]:
            return "uw-", Condition.VOWEL_NO_A
        return (
            ("uwa-", Condition.CONSONANT)
            if config.long_start
            else ("u-", Condition.CONSONANT)
        )

    if set_name == "2nd Set B":
        if s_type == StemType.ASPIRATED:
            return "ts-", Condition.ASPIRATED
        if s_type == StemType.S_STEM:
            return "t-", Condition.S_STEM
        if is_con:
            return "tsa-", Condition.CONSONANT
        return "ts-", Condition.VOWEL

    if set_name == "2nd Set A":
        return ("hi-", Condition.CONSONANT) if is_con else ("h-", Condition.VOWEL)

    if set_name == "2nd to 3rd":
        if not is_con:
            return ("hiy-", Condition.VOWEL)
        elif config.long_start:
            return ("hiya-", Condition.CONSONANT)
        else:
            return ("hi-", Condition.CONSONANT)

    if set_name == "1st Set A":
        return ("tsi-", Condition.CONSONANT) if is_con else ("k-", Condition.VOWEL)

    if set_name == "1st Set B":
        if s_type == StemType.ASPIRATED:
            return "akh-", Condition.ASPIRATED
        if s_type == StemType.S_STEM:
            return "akh-", Condition.S_STEM
        if is_con:
            return (
                ("aki-", Condition.CONSONANT)
                if config.use_aki_for_1st_set_b
                else ("ak-", Condition.CONSONANT)
            )
        return "akw-", Condition.VOWEL

    if set_name == "1st to 3rd":
        if not is_con:
            return ("tsiy-", Condition.VOWEL)
        elif config.long_start:
            return ("tsiya-", Condition.CONSONANT)
        else:
            return ("tsi-", Condition.CONSONANT)

    return "", Condition.CONSONANT


def attach_prefix(stem: str, prefix: str, condition: Condition) -> str:
    clean_prefix = prefix.replace("-", "")
    if clean_prefix == "ø":
        clean_prefix = ""

    if condition == Condition.METATHESIS_H_CONS:
        if stem[0] in VOWEL_SET:
            # ka + ah... -> khah...
            return clean_prefix[:-1] + "h" + stem[0] + stem[2:]
        else:
            # ka + n... -> kan... -> khan... (aspiration moves to prefix)
            return clean_prefix[:-1] + "h" + clean_prefix[-1:] + stem[0] + stem[2:]

    if condition == Condition.METATHESIS_VOWEL:
        if len(stem) > 1 and stem[1] == "h":
            # u- + ah... -> uhw...
            if clean_prefix == "u":
                # Check for double w formation from stem starting with w
                # e.g., u- + ahw... -> uwhw... (simplified to uwh...)
                res = "uwh" + stem[2:]
                if res.startswith("uwhw"):
                    return "uwh" + res[4:]
                return res
            return clean_prefix + stem[0] + stem[2:]

    if condition == Condition.A_REPLACE:
        if stem.startswith("a"):
            return clean_prefix + stem[1:]
    if condition == Condition.V:
        if stem.startswith("v"):
            return clean_prefix + stem[1:]

    return clean_prefix + stem


def detach_prefix(
    word: str,
    prefix: str,
    condition: Condition,
    metathesis_strategy: MetathesisStrategy = MetathesisStrategy.NONE,
) -> Optional[str]:
    # Derivation stripping logic
    clean_pref = prefix.replace("-", "")
    if clean_pref == "ø":
        clean_pref = ""

    if condition == Condition.METATHESIS_H_CONS:
        # Match 'kha' for 'ka'
        meta_pref = clean_pref[:-1] + "h" + clean_pref[-1:]
        if word.startswith(meta_pref):
            remainder = word[len(meta_pref) :]
            return remainder[0] + "h" + remainder[1:]

    # Heuristic for ka+h -> kh merger (for non-metathesis or implicit metathesis)
    # Only applies if the 'a' is missing (syncopated), e.g. khtosadi.
    # If word is kha..., we should let standard logic or METATHESIS_H_CONS handle it.
    if clean_pref == "ka" and word.startswith("kh") and not word.startswith("kha"):
        clean_pref = "k"

    if not word.startswith(clean_pref):
        return None

    remainder = word[len(clean_pref) :]
    stem = remainder

    if condition == Condition.METATHESIS_VOWEL:
        if clean_pref == "u" and word.startswith("uwh"):
            remainder = word[3:]
            # If remainder starts with a vowel, w was likely part of the stem (ahw...)
            # Preservation of /w/ before vowels (e.g. uhwolates -> ahwolates)
            if remainder and remainder[0] in VOWEL_SET:
                return "awh" + remainder
            return "ah" + remainder
        if remainder:
            stem = remainder[0:2] + remainder[2:] + "h"

    # Reverse Stem Transformations
    if condition == Condition.A_REPLACE:
        stem = "a" + remainder
    elif condition == Condition.V:
        stem = "v" + remainder

    # Regressions/Constraints
    if condition == Condition.ASPIRATED:
        # Restriction: ak- (akh-) before -i is not valid
        if clean_pref == "akh" and stem.startswith("i"):
            return None
        # Restriction: ts- before -ha is not valid
        if clean_pref == "ts" and stem.startswith("ha"):
            return None

    return stem


def apply_prepronominal(
    word: str, config: PrePronominalConfig, form_name: str
) -> List[str]:
    current_forms = [word]

    if config.distributive:
        new_forms = []
        for w in current_forms:
            if form_name == "infinitive" or (
                form_name == "imperative" and not config.distributiveImpIsFutProg
            ):
                new_forms.extend(["ts" + w, "ti" + w, "t" + w])
            else:
                new_forms.extend(["te" + w, "t" + w])
        current_forms = list(set(new_forms))

    if config.partitive:
        new_forms = []
        for w in current_forms:
            if form_name == "infinitive":
                new_forms.extend(["iy" + w, "i" + w, w])
            else:
                # Manual 'hn'/'hw' cases removed here as they are now handled
                # by the 'nh'/'wh' respelling reform in preprocessing.
                new_forms.extend(["ni" + w, "n" + w])
        current_forms = list(set(new_forms))

    if config.translocutive or (
        form_name == "imperative" and config.translocutiveImpOnly
    ):
        new_forms = []
        for w in current_forms:
            new_forms.extend(["wi" + w, "w" + w])
        current_forms = list(set(new_forms))

    return current_forms


def use_glottal_grade_for_set(set_name: str) -> bool:
    return set_name in ["2nd to 3rd", "1st to 3rd", "1st Set A"]


def use_glottal_grade(form: str, config: PronominalConfig) -> bool:
    return use_glottal_grade_for_set(get_pronominal_set_name(form, config))


def _drop_first_h(h_grade: str) -> str:
    idx = h_grade.find("h")
    if idx != -1:
        return h_grade[:idx] + h_grade[idx + 1 :]
    return h_grade


def _first_h_to_glottal(h_grade: str) -> str:
    idx = h_grade.find("h")
    if idx != -1:
        return h_grade[:idx] + "'" + h_grade[idx + 1 :]
    return h_grade


def prevent_C_glottal_cluster(form: str) -> str:
    # turn all sequences of (C+)' into '(C+)
    # capture consonants as [^aeiouv']
    return re.sub(r"([^aeiouv']+)'", r"'\1", form)


def recreate_C_glottal_clusters(surface: str) -> str:
    return re.sub(r"'([^aeiouv']+)", r"\1'", surface)


def _is_compatible_with_vowel_restoration(restored: str, syncopated: str) -> bool:
    if len(restored) - len(syncopated) not in [0, 1, 3]:
        return False
    i = 0
    j = 0
    quality_shift = False
    skipped = False
    skipped_idx = None
    while i < len(restored) and j < len(syncopated):
        if restored[i] == syncopated[j]:
            i += 1
            j += 1
        elif restored[i] == "i" and syncopated[j] == "a":
            # clothing words
            quality_shift = True
            i += 1
            j += 1
        else:
            if skipped:
                if (
                    # sometimes we will have a case like
                    #               1234
                    # syncopated:   tsgo
                    #                 ___
                    # restored:     tsihsgo
                    #               1234567
                    skipped_idx == i - 1
                    and restored[skipped_idx - 1] == "s"
                    and restored[i] == "h"
                    and restored[i + 1] == "s"
                ):
                    i += 2
                else:
                    return False
            elif restored[i] in VOWEL_SET:
                skipped = True
                skipped_idx = i
                i += 1
            else:
                return False
    if quality_shift:
        # can't handle this case
        if skipped:
            print("[WARNING] didn't plan for this case")

        return not skipped

    if not skipped:
        return i == len(restored) - 1 and restored[i] in VOWEL_SET

    return True


def _drop_h_in_deaffricated_lateral(h_grade: str):
    return h_grade.replace("lh", "tl", 1)


def possible_alternates(h_form: str, fix_clusters=True) -> list[str]:
    WAYS_TO_DROP = [
        lambda x: x,
        _drop_h_in_deaffricated_lateral,
        _drop_first_h,
        _first_h_to_glottal,
    ]

    return [
        prevent_C_glottal_cluster(way(h_form)) if fix_clusters else way(h_form)
        for way in WAYS_TO_DROP
    ]


def grades_are_compatible(*, h: str, glottal: str) -> bool:
    """Checks if `h` and `glottal` could be respective grades of the same stem or root"""

    for h_dropped in possible_alternates(h):
        if h_dropped == glottal:
            return True
        if _is_compatible_with_vowel_restoration(glottal, h_dropped):
            return True

    return False
