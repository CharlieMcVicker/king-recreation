from enum import Enum

from morphology.h_alternation import grades_are_compatible
from morphology.metathesis import demetathesize_h, metathesize_h
from morphology.phonology_data import VOWEL_SET


class Constraint(Enum):
    NONE = "none"
    PRE_V = "pre_v"
    PRE_C = "pre_c"
    PRE_S = "pre_s"
    PRE_C_NO_S = "pre_c_no_s"

    def matches(self, root: str) -> bool:
        if self == Constraint.NONE or len(root) == 0:
            return True
        elif self == Constraint.PRE_S:
            return root.startswith("hs")

        wants_vowel = self == Constraint.PRE_V
        is_vowel = root[0] in VOWEL_SET

        if self == Constraint.PRE_C_NO_S:
            if root.startswith("s") or root.startswith("hs"):
                return False

        return wants_vowel == is_vowel


class MiddleVoice(Enum):
    NONE = "none"
    AT = "at"
    AT_PRE_C = "at_pre_c"
    ATA = "ata"
    ATA_LONG = "ata_:"
    ATAT = "atat"
    ATI = "ati"
    ATI_LONG = "ati_:"
    ATI_V = "ati_v"
    ALI = "ali"
    AL_ALI = "al_ali"
    # ALH_ALI = "alh_ali"

    def try_strip_form(self, form: str) -> str | None:
        """
        messy bad, no good h alt checking
        """

        test_h, test_g, _ = self.get_form()

        if form.startswith(test_g):
            return form[len(test_g) :]
        elif form.startswith(test_h):
            return form[len(test_h) :]
        else:
            return None

    def try_strip(
        self, h_grade: str, g_grade: str | None, allow_metathesis: bool
    ) -> tuple[str, str | None] | None:
        if self == MiddleVoice.NONE:
            return h_grade, g_grade

        test_h, test_g, condition = self.get_form()
        h_grade_stripped = None
        if allow_metathesis:
            h_grade_stripped = demetathesize_h(test_h, h_grade)

        elif h_grade.startswith(test_h):
            h_grade_stripped = h_grade[len(test_h) :]

        if h_grade_stripped is not None and (
            g_grade is None or g_grade.startswith(test_g)
        ):
            g_grade_stripped = g_grade[len(test_g) :] if g_grade is not None else None

            if self == MiddleVoice.ATI_V:
                h_grade_stripped = "v" + h_grade_stripped
                g_grade_stripped = (
                    "v" + g_grade_stripped if g_grade_stripped is not None else None
                )

            if self in [MiddleVoice.ATI_LONG, MiddleVoice.ATA_LONG]:
                h_grade_stripped = ":" + h_grade_stripped
                g_grade_stripped = (
                    ":" + g_grade_stripped if g_grade_stripped is not None else None
                )

            return (h_grade_stripped, g_grade_stripped)
        else:
            return None

    def apply(self, stem: str, is_glottal_grade: bool, allow_metathesis: bool) -> str:
        if self == MiddleVoice.NONE:
            return stem

        h_grade, g_grade, _ = self.get_form()
        if self in [MiddleVoice.ATI_V, MiddleVoice.ATI_LONG, MiddleVoice.ATA_LONG]:
            # drop v
            stem = ">" + stem

        if is_glottal_grade:
            return g_grade + "-" + stem
        else:
            if self.metathesizing_form() and allow_metathesis:
                h_grade, stem = metathesize_h(h_grade, stem)
            return h_grade + "-" + stem

    def get_form(self) -> tuple[str, str, Constraint]:
        return MiddleVoice.form_maps()[self]

    def metathesizing_form(self) -> bool:
        META_FORMS = [
            MiddleVoice.ALI,
            MiddleVoice.AT,
        ]
        return self in META_FORMS

    @staticmethod
    def form_maps() -> dict["MiddleVoice", tuple[str, str, Constraint]]:
        return {
            MiddleVoice.NONE: ("", "", Constraint.NONE),
            MiddleVoice.AT: ("at", "at", Constraint.PRE_V),
            MiddleVoice.AT_PRE_C: ("at", "at", Constraint.PRE_C_NO_S),
            MiddleVoice.ATA: ("ata", "ata", Constraint.PRE_C),
            MiddleVoice.ATA_LONG: ("ata", "ata", Constraint.NONE),
            MiddleVoice.ATAT: ("atat", "atat", Constraint.PRE_V),
            MiddleVoice.ATI: ("ati", "ati", Constraint.PRE_C),
            MiddleVoice.ATI_LONG: ("ati", "ati", Constraint.NONE),
            MiddleVoice.ATI_V: ("ati", "ati", Constraint.PRE_V),
            MiddleVoice.ALI: ("ali", "ali", Constraint.PRE_C),
            MiddleVoice.AL_ALI: ("al", "ali", Constraint.PRE_C),
            # MiddleVoice.ALH_ALI: ("alh", "ali", Constraint.PRE_C_NO_S),
        }

    @staticmethod
    def identify_middle_voice(
        h_grade: str, g_grade: str | None, log: bool = False
    ) -> list[tuple["MiddleVoice", tuple[str, str | None], bool]]:
        possibilities = []
        for voice in MiddleVoice:
            for allow_meta in [False, True] if voice.metathesizing_form() else [False]:
                _, _, condition = voice.get_form()
                res = voice.try_strip(h_grade, g_grade, allow_meta)
                match_h = res and condition.matches(res[0])
                match_g = res and (res[1] is None or condition.matches(res[1]))
                grades_match = res and (
                    res[1] is None or grades_are_compatible(h=res[0], glottal=res[1])
                )
                if log:
                    print(
                        h_grade,
                        "|",
                        g_grade,
                        voice.value,
                        res is not None,
                        match_h,
                        match_g,
                        grades_match,
                    )
                    if res:
                        print("\t", res[0], res[1])
                if res and match_h and match_g and grades_match:
                    possibilities.append((voice, res, allow_meta))

        return possibilities
