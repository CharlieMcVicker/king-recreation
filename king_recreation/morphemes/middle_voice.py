from enum import Enum
from typing import List, Optional, Tuple


class MiddleVoice(Enum):
    NONE = "none"
    AT = "at"
    ATA = "ata"
    ATAT = "atat"
    ALI = "ali"
    AL_ALI = "al_ali"

    def try_strip_form(self, form: str):
        """
        messy bad, no good h alt checking
        """

        test_h, test_g = self.get_form()

        if form.startswith(test_g):
            return form[len(test_g) :]
        elif form.startswith(test_h):
            return form[len(test_h) :]
        else:
            return None

    def try_strip(
        self, h_grade: str, g_grade: Optional[str]
    ) -> Optional[Tuple[str, Optional[str]]]:

        test_h, test_g = self.get_form()

        if h_grade.startswith(test_h) and (
            g_grade is None or g_grade.startswith(test_g)
        ):
            return (
                h_grade[len(test_h) :],
                g_grade[len(test_g) :] if g_grade is not None else None,
            )
        else:
            return None

    def apply(self, stem: str, is_glottal_grade: bool):
        h_grade, g_grade = self.get_form()
        if self == MiddleVoice.NONE:
            return stem
        elif is_glottal_grade:
            return g_grade + "-" + stem
        else:
            return h_grade + "-" + stem

    def get_form(self):
        return MiddleVoice.form_maps()[self]

    @staticmethod
    def form_maps():
        return {
            MiddleVoice.NONE: ("", ""),
            MiddleVoice.AT: ("at", "at"),
            MiddleVoice.ATA: ("ata", "ata"),
            MiddleVoice.ATAT: ("atat", "atat"),
            MiddleVoice.ALI: ("ali", "ali"),
            MiddleVoice.AL_ALI: ("al", "ali"),
        }

    @staticmethod
    def identify_middle_voice(
        h_grade: str, g_grade: Optional[str]
    ) -> List[Tuple["MiddleVoice", Tuple[str, Optional[str]]]]:
        possibilities = []
        for voice in MiddleVoice:
            res = voice.try_strip(h_grade, g_grade)
            if res:
                possibilities.append((voice, res))

        return possibilities
