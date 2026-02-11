from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union

from king_recreation.phonology_data import VOWEL_SET
from king_recreation.tone.utils import TONE_VALUE_TO_ENUM, Consonant, Vowel, VowelTone


@dataclass(frozen=True)
class MorphemeBoundary:
    def __str__(self):
        return "-"


def tone_sequence_from_corpus_form(
    s: str,
) -> List[Union[Consonant, Vowel, MorphemeBoundary]]:
    if not s:
        return []

    res = []
    idx = 0
    while idx < len(s):
        char = s[idx]
        if char == "-":
            res.append(MorphemeBoundary())
            idx += 1
            continue

        if char in VOWEL_SET:
            # Look ahead for tone digits or "?"
            tone_start = idx + 1
            tone_end = tone_start
            while tone_end < len(s) and s[tone_end].isdigit():
                tone_end += 1

            tone_str = s[tone_start:tone_end]
            tone_enum = TONE_VALUE_TO_ENUM.get(tone_str)
            if not tone_enum:
                tone_enum = VowelTone.l

            res.append(
                Vowel(
                    quality=char,
                    tone=tone_enum,
                )
            )
            idx = tone_end
        else:
            # Consonant or glottal stop
            res.append(Consonant(value=char))
            idx += 1
    return res


class LocalHighTone(Enum):
    NONE = 0
    TWO_PREV = 1
    PREV = 2

    def advance(self):
        """
        Move forward in syllables, and update local hightone counter
        """
        if self in [self.NONE, self.TWO_PREV]:
            return self.NONE
        else:
            return self.TWO_PREV


class Tonicity(Enum):
    TONIC = "tonic"
    ATONIC = "atonic"
    INFINITIVE = "infinitive"


class Environment(Enum):
    SPREAD = "spread"
    NO_SPREAD = "no_spread"
    BLOCKED = "blocked"

    @staticmethod
    def from_state(
        lh: LocalHighTone, prev_long: bool, tonicity: Tonicity = Tonicity.TONIC
    ) -> "Environment":
        if tonicity == Tonicity.ATONIC:
            return Environment.BLOCKED

        if lh == lh.PREV:
            return Environment.BLOCKED

        # Determine raw environment
        raw_env = (
            Environment.SPREAD
            if (prev_long and lh != lh.TWO_PREV)
            else Environment.NO_SPREAD
        )

        if tonicity == Tonicity.INFINITIVE and raw_env == Environment.NO_SPREAD:
            return Environment.BLOCKED

        return raw_env


class GlottalPosition(Enum):
    PRE_C = "'C"
    POST_C = "C'"
    NO_C = "'"


@dataclass(frozen=True)
class H1Config:
    historically_long: bool
    glottal_position: GlottalPosition
    env: Environment


# Intermediate "lexed" form between surface and underlying
@dataclass(frozen=True)
class HistoricalVowel:
    quality: str
    length: bool  # True for long, False for short
    glottal_position: Union[GlottalPosition, None] = None
    h2: bool = False
    derived_env: Optional["Environment"] = field(default=None, compare=False)

    def __str__(self):
        v = self.quality * (2 if self.length else 1)
        if self.glottal_position in [GlottalPosition.PRE_C, GlottalPosition.NO_C]:
            v += "'"
        if self.h2:
            v += "/"
        return v


@dataclass(frozen=True)
class LexedForm:
    tokens: List[Union[HistoricalVowel, Consonant, MorphemeBoundary]]

    def __str__(self):
        res = []
        pending_post_c = False
        for i, token in enumerate(self.tokens):
            if isinstance(token, MorphemeBoundary):
                res.append("-")
            elif isinstance(token, Consonant):
                res.append(token.value)
                if pending_post_c:
                    res.append("'")
                    pending_post_c = False
            else:
                if pending_post_c:
                    # Should not normally happen if POST_C follows its rules,
                    # but if it does, the glottal surfaces here.
                    res.append("'")
                    pending_post_c = False

                res.append(str(token))
                if token.glottal_position == GlottalPosition.POST_C:
                    pending_post_c = True

        if pending_post_c:
            res.append("'")
        return "".join(res)

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self) == other
        if isinstance(other, LexedForm):
            return self.tokens == other.tokens
        return False

    @classmethod
    def from_str(cls, s: str) -> "LexedForm":
        """
        Robustly parse a string representation back into a LexedForm.
        """
        tokens = []
        idx = 0
        while idx < len(s):
            char = s[idx]
            if char in VOWEL_SET:
                start_v = idx
                while idx < len(s) and s[idx] == char:
                    idx += 1
                length = (idx - start_v) > 1
                quality = char
                g_pos = None

                # Check for PRE_C / NO_C glottal (V')
                if idx < len(s) and s[idx] == "'":
                    # Peek ahead to see if it's followed by C or end of string
                    has_following_c = False
                    for k in range(idx + 1, len(s)):
                        if s[k] not in VOWEL_SET and s[k] != "'" and s[k] != "-":
                            has_following_c = True
                            break
                    g_pos = (
                        GlottalPosition.PRE_C
                        if has_following_c
                        else GlottalPosition.NO_C
                    )
                    idx += 1

                h2 = False
                if idx < len(s) and s[idx] == "/":
                    h2 = True
                    idx += 1

                tokens.append(HistoricalVowel(quality, length, g_pos, h2))
            elif char == "-":
                tokens.append(MorphemeBoundary())
                idx += 1
            else:
                # Consonant or glottal
                tokens.append(Consonant(char))
                # Check for POST_C (C')
                if char != "'" and idx + 1 < len(s) and s[idx + 1] == "'":
                    # Mark the PREVIOUS vowel as POST_C
                    marked = False
                    for k in range(len(tokens) - 2, -1, -1):
                        if isinstance(tokens[k], HistoricalVowel):
                            v = tokens[k]
                            tokens[k] = HistoricalVowel(
                                v.quality, v.length, GlottalPosition.POST_C
                            )
                            marked = True
                            break
                    if marked:
                        idx += 1  # skip the '
                idx += 1
        return cls(tokens)
