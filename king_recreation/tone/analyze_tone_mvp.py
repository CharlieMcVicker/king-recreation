import io
import itertools
import json
import os
from csv import DictReader, DictWriter
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Union

from king_recreation.paths import (
    cherokee_nation_dictionary_path,
    corpus_to_cnd_path,
    reconstructable_verbs_path,
    stems_with_tone_corpus_path,
    underlying_stems_path,
)
from king_recreation.phonology_data import VOWEL_SET
from king_recreation.reconstruct_from_roots import ReconstructibleVerb
from king_recreation.tone.utils import (
    TONE_VALUE_TO_ENUM,
    Consonant,
    Vowel,
    VowelTone,
    apply_tone_to_segmentation,
    get_tone_sequence_for_form,
    strip_morpheme_boundaries,
)


def load_data():
    """Load the necessary data for tone analysis."""
    with open(reconstructable_verbs_path, "r") as f:
        reconstructable_verbs_raw = json.load(f)
    verbs = [ReconstructibleVerb.from_dict(v) for v in reconstructable_verbs_raw]

    with open(corpus_to_cnd_path, "r") as f:
        reader = DictReader(f)
        corpus_id_to_entries = {int(r["corpus_id"]): r for r in reader}

    with open(cherokee_nation_dictionary_path, "r") as f:
        content = f.read()
        if content.startswith("\ufeff"):
            content = content[1:]
        reader = DictReader(io.StringIO(content))
        # Entry No. is the primary key used in corpus_to_cnd mapping
        cnd_corpus = {r.get("Entry No.", "").strip(): r for r in reader}

    return verbs, cnd_corpus, corpus_id_to_entries


def is_eligible(verb: ReconstructibleVerb) -> bool:
    """
    Filter verbs based on the Tone MVP criteria:
    - No prepronominal prefixes
    - No middle voice
    - No animate object-pronouns
    - Root does not start with 'a'
    """
    # 1. No prepronominal prefixes (translocutive, partitive, distributive)
    pre = verb.config.pre
    if (
        pre.translocutive
        or pre.translocutiveImpOnly
        or pre.partitive
        or pre.distributive
    ):
        return False

    # 2. No middle voice (MiddleVoice.NONE)
    if verb.config.pron.middle_voice.value != "none":
        return False

    if verb.config.pron.use_3rd_person_object:
        return False

    # 3. Root does not start with 'a' (specifically roots beginning with vowel 'a')
    if verb.h_grade_root.lower().startswith("a"):
        return False

    return True


def get_stem_tones(
    verb: ReconstructibleVerb, form_name: str, cnd_corpus, corpus_id_to_entries
):
    segmented = verb.segmented_forms.get(form_name)
    if not segmented:
        return None

    # Access each form and the tones on it in the parsed format from utils
    # tone_sequence is a List[Union[Vowel, Consonant]]
    tone_sequence: List[Union[Vowel, Consonant]] = get_tone_sequence_for_form(
        verb, form_name, cnd_corpus, corpus_id_to_entries
    )

    if not tone_sequence:
        return None

    # Access the tones on it (parsed format)
    # Example of how to use it:
    # vowel_tones = [str(t.tone) for t in tone_sequence if isinstance(t, Vowel)]

    # --- START MVP ANALYSIS LOGIC ---
    # (User will implement H2 and H1 logic here)
    combined = apply_tone_to_segmentation(segmented, tone_sequence)
    parts = combined.split("-")
    end_parts = 3 if verb.post_root_morpheme else 2
    stem_tones = "-".join(parts[-end_parts:]) if len(parts) >= end_parts else combined

    return stem_tones


FORMS = [
    "present",
    "present_1sg",
    "imperfective",
    "perfective",
    "imperative",
    "infinitive",
]


def write_elligible_verbs(verbs, cnd_corpus, corpus_id_to_entries):

    eligible_count = 0

    # Iterate over every verb in reconstructible verbs
    rows = []
    for verb in verbs:
        # Apply filtering criteria
        if not is_eligible(verb):
            continue

        eligible_count += 1
        stem_tones = {
            fn: get_stem_tones(verb, fn, cnd_corpus, corpus_id_to_entries)
            for fn in FORMS
        }

        rows.append(
            (
                verb,
                {
                    "corpus_id": verb.corpus_id,
                    "definition": verb.definition,
                    **stem_tones,
                },
            )
        )

    # Write all rows to disk as a new - stems_with_tone_corpus.csv
    if rows:
        with open(stems_with_tone_corpus_path, "w", newline="") as f:
            # Use the second element of the tuple which is the dictionary
            writer = DictWriter(f, fieldnames=rows[0][1].keys())
            writer.writeheader()
            writer.writerows([row[1] for row in rows])

        print(
            f"\nScaffold complete. Processed {len(verbs)} verbs, {eligible_count} were eligible for analysis."
        )

    return rows


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


def get_tonicity_for_form(verb: ReconstructibleVerb, form_name: str) -> Tonicity:
    """Determine the tonicity for a given verb form."""
    if form_name == "infinitive":
        return Tonicity.INFINITIVE

    if form_name == "imperative" and not verb.config.stative:
        pre = verb.config.pre
        has_pre = (
            pre.translocutive
            or pre.translocutiveImpOnly
            or pre.partitive
            or pre.distributive
        )
        if not has_pre:
            return Tonicity.ATONIC

    return Tonicity.TONIC


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


# to be populated from docs/tone_mvp.md
H1_INFERENCES = {
    # Long PRE_C
    H1Config(True, GlottalPosition.PRE_C, Environment.SPREAD): [
        [VowelTone.lh, VowelTone.hl]
    ],
    H1Config(True, GlottalPosition.PRE_C, Environment.NO_SPREAD): [
        [VowelTone.hh],
    ],
    H1Config(True, GlottalPosition.PRE_C, Environment.BLOCKED): [[VowelTone.lf]],
    # Short PRE_C
    H1Config(False, GlottalPosition.PRE_C, Environment.SPREAD): [
        [VowelTone.lh, VowelTone.hl]
    ],
    H1Config(False, GlottalPosition.PRE_C, Environment.NO_SPREAD): [
        [VowelTone.hl],
    ],
    H1Config(False, GlottalPosition.PRE_C, Environment.BLOCKED): [[VowelTone.lf]],
    # Long NO_C
    H1Config(True, GlottalPosition.NO_C, Environment.SPREAD): [
        [
            VowelTone.hh,
            Consonant(
                "'",
            ),
        ],
        [
            VowelTone.lh,
            VowelTone.h,
            Consonant(
                "'",
            ),
        ],
    ],
    H1Config(True, GlottalPosition.NO_C, Environment.NO_SPREAD): [
        [
            VowelTone.hh,
            Consonant(
                "'",
            ),
        ]
    ],
    H1Config(True, GlottalPosition.NO_C, Environment.BLOCKED): [
        [
            VowelTone.l,
            Consonant(
                "'",
            ),
        ]
    ],
    # Short NO_C
    H1Config(False, GlottalPosition.NO_C, Environment.SPREAD): [
        [
            VowelTone.lh,
            VowelTone.h,
            Consonant(
                "'",
            ),
        ]
    ],
    H1Config(False, GlottalPosition.NO_C, Environment.NO_SPREAD): [
        [
            VowelTone.h,
            Consonant(
                "'",
            ),
        ]
    ],
    H1Config(False, GlottalPosition.NO_C, Environment.BLOCKED): [
        [
            VowelTone.l,
            Consonant(
                "'",
            ),
        ]
    ],
    # Long POST_C
    H1Config(True, GlottalPosition.POST_C, Environment.SPREAD): [[VowelTone.hh]],
    H1Config(True, GlottalPosition.POST_C, Environment.NO_SPREAD): [[VowelTone.hh]],
    H1Config(True, GlottalPosition.POST_C, Environment.BLOCKED): [[VowelTone.ll]],
    # Short POST_C
    H1Config(False, GlottalPosition.POST_C, Environment.SPREAD): [
        [VowelTone.lh, VowelTone.h]
    ],
    H1Config(False, GlottalPosition.POST_C, Environment.NO_SPREAD): [
        [VowelTone.h],
        [
            VowelTone.h,
            Consonant(
                "'",
            ),
        ],
    ],
    H1Config(False, GlottalPosition.POST_C, Environment.BLOCKED): [[VowelTone.l]],
}


def get_possible_glottal_positions(
    env: Environment,
    tone: VowelTone,
    prev_tone: VowelTone = None,
    has_glottal: bool = False,
    has_following_c: bool = False,
) -> List[H1Config]:
    """
    Search H1_INFERENCES for underlying configurations that could produce the observed tone.
    """
    results = []
    for config, sequences in H1_INFERENCES.items():
        if config.env != env:
            continue

        for seq in sequences:
            # Check for glottal stop in sequence
            seq_has_glottal = any(
                isinstance(s, Consonant) and s.value == "'" for s in seq
            )
            if seq_has_glottal != has_glottal:
                continue

            # Additional filter for following consonant
            if has_following_c:
                if config.glottal_position == GlottalPosition.NO_C:
                    continue
            else:
                if config.glottal_position in [
                    GlottalPosition.PRE_C,
                    GlottalPosition.POST_C,
                ]:
                    continue

            # Extract just the vowel tones from the sequence
            v_tones = [s for s in seq if isinstance(s, VowelTone)]

            if len(v_tones) == 1:
                if v_tones[0] == tone:
                    results.append(config)
                    break
            elif len(v_tones) == 2:
                # Sequence match: current tone must match LAST, previous tone should match first
                if v_tones[1] == tone and (
                    prev_tone is None or v_tones[0] == prev_tone
                ):
                    results.append(config)
                    break
    return results


def predict_h1_for_form(
    form_str: str, tonicity: Tonicity = Tonicity.TONIC
) -> List[tuple[Vowel, List[H1Config]]]:
    """
    Wrapper around generate_underlying_forms to maintain compatibility with tests.
    """
    if not form_str:
        return []

    tone_sequence = tone_sequence_from_corpus_form(form_str)
    surface_vowels = [s for s in tone_sequence if isinstance(s, Vowel)]

    candidates = generate_underlying_forms(form_str, tonicity=tonicity)

    results = []
    # For each vowel index, collect unique H1Configs from all candidates
    for i, suv in enumerate(surface_vowels):
        configs = set()
        for cand in candidates:
            # LexedForm.tokens contains MorphemeBoundary and Consonants too.
            # But the number of HistoricalVowels matches surface_vowels.
            hvs = [t for t in cand.tokens if isinstance(t, HistoricalVowel)]
            if i < len(hvs):
                hv = hvs[i]
                if hv.glottal_position is not None and hv.derived_env is not None:
                    configs.add(
                        H1Config(hv.length, hv.glottal_position, hv.derived_env)
                    )

        if configs:
            # Sort for deterministic test results
            results.append(
                (
                    suv,
                    sorted(
                        list(configs),
                        key=lambda x: (x.glottal_position.value, x.historically_long),
                    ),
                )
            )

    return results


def generate_underlying_forms(
    form_str: str,
    initial_lh: LocalHighTone = LocalHighTone.NONE,
    initial_pl: bool = False,
    tonicity: Tonicity = Tonicity.TONIC,
) -> List[LexedForm]:
    """
    Generate all possible underlying form objects (LexedForm) from a surface form string.
    """
    if not form_str:
        return []

    # Use form_str directly to preserve boundaries if any
    tone_sequence = tone_sequence_from_corpus_form(form_str)
    prev_tone = None

    # Path state: (tokens, lh, pl, pt, skip_surface_glottal)
    initial_path = ([], initial_lh, initial_pl, prev_tone, False)
    paths = [initial_path]

    for i, seg in enumerate(tone_sequence):
        new_paths = []
        for tokens, lh, pl, pt, skip_surface_glottal in paths:
            if isinstance(seg, MorphemeBoundary):
                new_paths.append((tokens + [seg], lh, pl, pt, False))
            elif isinstance(seg, Consonant):
                if seg.value == "'":
                    if skip_surface_glottal:
                        # This surface glottal was already accounted for by the preceding vowel
                        new_paths.append((tokens, lh, pl, pt, False))
                    else:
                        # Unaccounted glottal, keep it
                        new_paths.append((tokens + [seg], lh, pl, pt, False))
                else:
                    # Normal consonant
                    new_paths.append((tokens + [seg], lh, pl, pt, False))
            elif isinstance(seg, Vowel):
                has_glottal = False
                if i + 1 < len(tone_sequence):
                    next_seg = tone_sequence[i + 1]
                    if isinstance(next_seg, Consonant) and next_seg.value == "'":
                        has_glottal = True

                has_following_c = False
                for j in range(i + 1, len(tone_sequence)):
                    next_seg = tone_sequence[j]
                    if isinstance(next_seg, Consonant):
                        if next_seg.value != "'":
                            has_following_c = True
                            break
                    elif isinstance(next_seg, Vowel):
                        break

                env = Environment.from_state(lh, pl, tonicity)
                configs = []
                if has_glottal or (
                    seg.tone
                    and seg.tone
                    in [
                        VowelTone.hh,
                        VowelTone.h,
                        VowelTone.hl,
                        VowelTone.lf,
                        VowelTone.lh,
                    ]
                ):
                    configs = get_possible_glottal_positions(
                        env, seg.tone, pt, has_glottal, has_following_c
                    )

                # Determine candidates for this vowel
                candidates = []

                # 1. Plain vowel (always try)
                is_long = seg.tone and len(seg.tone.value) == 2
                env = Environment.from_state(lh, pl, tonicity)
                next_lh = lh.advance()
                if env == Environment.SPREAD and is_long:
                    next_lh = LocalHighTone.PREV

                candidates.append(
                    {
                        "hv": HistoricalVowel(
                            seg.quality, is_long, None, derived_env=env
                        ),
                        "next_lh": next_lh,
                        "skip_g": False,
                    }
                )

                # 2. H1 configurations
                for cfg in configs:
                    candidates.append(
                        {
                            "hv": HistoricalVowel(
                                seg.quality,
                                cfg.historically_long,
                                cfg.glottal_position,
                                derived_env=env,
                            ),
                            "next_lh": LocalHighTone.PREV,
                            "skip_g": has_glottal,
                        }
                    )

                # 3. H2 variants for all above
                # H2 only occurs on the last mora of a segment.
                is_segment_end = False
                is_last_vowel_in_segment = True
                for k in range(i + 1, len(tone_sequence)):
                    if isinstance(tone_sequence[k], Vowel):
                        is_last_vowel_in_segment = False
                        break
                    if isinstance(tone_sequence[k], MorphemeBoundary):
                        break

                if is_last_vowel_in_segment:
                    is_segment_end = True

                h2_eligible = (
                    is_segment_end and seg.tone and seg.tone.value.endswith("3")
                )
                if h2_eligible:
                    # Lookahead for next vowel length for H2 blocking state
                    next_v_long = False
                    for k in range(i + 1, len(tone_sequence)):
                        if isinstance(tone_sequence[k], Vowel):
                            next_v_long = len(tone_sequence[k].tone.value) == 2
                            break

                    h2_blocks = seg.tone == VowelTone.hh or (
                        seg.tone == VowelTone.h and next_v_long
                    )
                    h2_next_lh = LocalHighTone.PREV if h2_blocks else lh.advance()

                    h2_candidates = []
                    for cand in candidates:
                        # Copy and set h2=True
                        h2_cand = dict(cand)
                        h2_cand["hv"] = HistoricalVowel(
                            cand["hv"].quality,
                            cand["hv"].length,
                            cand["hv"].glottal_position,
                            h2=True,
                            derived_env=env,
                        )
                        h2_cand["next_lh"] = h2_next_lh
                        h2_candidates.append(h2_cand)
                    candidates.extend(h2_candidates)

                for cand in candidates:
                    hv = cand["hv"]
                    new_paths.append(
                        (
                            tokens + [hv],
                            cand["next_lh"],
                            hv.length,
                            seg.tone,
                            cand["skip_g"],
                        )
                    )
        paths = new_paths

    return [LexedForm(p[0]) for p in paths]


def predict_underlying_form(verb, forms, form_name):
    # Determine the tone sequence for the given form
    form_str = forms[form_name]
    tonicity = get_tonicity_for_form(verb, form_name)
    return generate_underlying_forms(form_str, tonicity=tonicity)


def infer_surface_forms(
    lexed: Union[LexedForm, str],
    initial_lh: LocalHighTone = LocalHighTone.NONE,
    tonicity: Tonicity = Tonicity.TONIC,
) -> List[str]:
    """
    Forward inference: Generate possible surface forms from a LexedForm (or string).
    """
    if isinstance(lexed, str):
        lexed = LexedForm.from_str(lexed)

    tokens = lexed.tokens

    def solve(
        u_idx: int, local_high: LocalHighTone, prev_long: bool, surface_tones: List[str]
    ) -> List[str]:
        if u_idx >= len(tokens):
            res = []
            for k, token in enumerate(tokens):
                if isinstance(token, Consonant):
                    res.append(token.value)
                elif isinstance(token, MorphemeBoundary):
                    res.append("-")
                else:
                    res.append(surface_tones[k])
            return ["".join(res)]

        token = tokens[u_idx]
        if isinstance(token, MorphemeBoundary):
            return solve(u_idx + 1, local_high, prev_long, surface_tones)

        if isinstance(token, Consonant):
            return solve(u_idx + 1, local_high, prev_long, surface_tones)

        # It's a HistoricalVowel
        g_pos = token.glottal_position
        h2 = token.h2

        # Determine H2 effect
        h2_tone_enum = None
        h2_blocks = False
        if h2:
            next_v = None
            for k in range(u_idx + 1, len(tokens)):
                if isinstance(tokens[k], MorphemeBoundary):
                    break
                if isinstance(tokens[k], HistoricalVowel):
                    next_v = tokens[k]
                    break
            is_next_long = next_v.length if next_v else False

            if token.length:
                h2_tone_enum = VowelTone.hh if is_next_long else VowelTone.lh
            else:
                h2_tone_enum = VowelTone.h

            h2_blocks = h2_tone_enum == VowelTone.hh or (
                h2_tone_enum == VowelTone.h and is_next_long
            )

        results = []
        if g_pos:
            env = Environment.from_state(local_high, prev_long, tonicity)
            cfg = H1Config(token.length, g_pos, env)
            sequences = H1_INFERENCES.get(cfg, [])
            if sequences:
                for seq in sequences:
                    new_tones = list(surface_tones)
                    v_tones = [item for item in seq if isinstance(item, VowelTone)]
                    c_inline = [
                        item.value for item in seq if isinstance(item, Consonant)
                    ]

                    # If h2 is present, current vowel tone must match h2_tone
                    if h2_tone_enum and v_tones[-1] != h2_tone_enum:
                        continue

                    # For POST_C, the "spreading" tone actually applies to the PRECEDING vowel.
                    if g_pos == GlottalPosition.POST_C:
                        if len(v_tones) == 2:
                            # v_tones[0] goes to preceding vowel
                            # v_tones[1] goes to current vowel
                            prev_v_idx = -1
                            for k in range(u_idx - 1, -1, -1):
                                if isinstance(tokens[k], HistoricalVowel):
                                    prev_v_idx = k
                                    break
                            if prev_v_idx != -1:
                                new_tones[prev_v_idx] = (
                                    tokens[prev_v_idx].quality + v_tones[0].value
                                )
                            new_tones[u_idx] = (
                                token.quality + v_tones[1].value + "".join(c_inline)
                            )
                        else:
                            # Single tone for POST_C
                            new_tones[u_idx] = (
                                token.quality + v_tones[0].value + "".join(c_inline)
                            )
                    else:
                        # PRE_C or NO_C
                        current_v_str = (
                            token.quality + v_tones[-1].value + "".join(c_inline)
                        )
                        new_tones[u_idx] = current_v_str

                        if len(v_tones) == 2:
                            # Apply spreading tone to preceding vowel
                            prev_v_idx = -1
                            for k in range(u_idx - 1, -1, -1):
                                if isinstance(tokens[k], HistoricalVowel):
                                    prev_v_idx = k
                                    break
                            if prev_v_idx != -1:
                                new_tones[prev_v_idx] = (
                                    tokens[prev_v_idx].quality + v_tones[0].value
                                )

                    results.extend(
                        solve(u_idx + 1, LocalHighTone.PREV, token.length, new_tones)
                    )
            else:
                # No H1 rule, but what if H2 is present?
                if h2:
                    new_tones = list(surface_tones)
                    new_tones[u_idx] = token.quality + h2_tone_enum.value
                    next_lh = LocalHighTone.PREV if h2_blocks else local_high.advance()
                    results.extend(solve(u_idx + 1, next_lh, token.length, new_tones))
                else:
                    # No rule: Fallback to Low
                    new_tones = list(surface_tones)
                    if new_tones[u_idx] is None:
                        new_tones[u_idx] = token.quality + (
                            "22" if token.length else "2"
                        )
                    results.extend(
                        solve(u_idx + 1, local_high.advance(), token.length, new_tones)
                    )
        elif h2:
            # H2 only
            new_tones = list(surface_tones)
            if new_tones[u_idx] is None:
                new_tones[u_idx] = token.quality + h2_tone_enum.value

            next_lh = LocalHighTone.PREV if h2_blocks else local_high.advance()
            results.extend(solve(u_idx + 1, next_lh, token.length, new_tones))
        else:
            # Plain vowel
            env = Environment.from_state(local_high, prev_long, tonicity)
            new_tones = list(surface_tones)
            if new_tones[u_idx] is None:
                if env == Environment.SPREAD and token.length:
                    new_tones[u_idx] = token.quality + "33"
                    next_lh = LocalHighTone.PREV
                else:
                    new_tones[u_idx] = token.quality + ("22" if token.length else "2")
                    next_lh = local_high.advance()

            results.extend(solve(u_idx + 1, next_lh, token.length, new_tones))

        return results

    return solve(0, initial_lh, False, [None] * len(tokens))


def check_prediction(
    underlying_form: str,
    target_surface: str,
    initial_lh: LocalHighTone = LocalHighTone.NONE,
    tonicity: Tonicity = Tonicity.TONIC,
) -> bool:
    """
    Integrity check: Can this underlying form generate the target surface form?
    """
    # Normalize clean_target by parsing and re-serializing to ensure consistent tone representation
    clean_target = strip_morpheme_boundaries(target_surface)
    seq = tone_sequence_from_corpus_form(clean_target)
    normalized_target = "".join(str(s) for s in seq)

    surface_candidates = infer_surface_forms(
        underlying_form, initial_lh=initial_lh, tonicity=tonicity
    )
    stripped_candidates = [strip_morpheme_boundaries(c) for c in surface_candidates]
    return normalized_target in stripped_candidates


def diagnose_mismatch(
    verb, surface, expected_ending, tonicity: Tonicity = Tonicity.TONIC
):
    print(f"    Mismatch: {verb.definition[:30]}... | Surface: {surface}")

    underlying_candidates = generate_underlying_forms(surface, tonicity=tonicity)
    valid_candidates = [
        str(uf)
        for uf in underlying_candidates
        if check_prediction(str(uf), surface, tonicity=tonicity)
    ]

    # 1. Check for Length or quality Mismatch (Valid UF exists but different ending)
    if valid_candidates:
        print(f"      Found {len(valid_candidates)} valid underlying forms:")
        for uf in valid_candidates:
            print(f"        - {uf}")
        # Check if any is 'close' (e.g. length diff)
        # Simplify: just report them. User can see.

    # 2. Check for Start State Blocked (for Imperative/21 tone)
    # Try assuming PREVIOUS High (BLOCKED environment)
    candidates_blocked = generate_underlying_forms(
        surface, initial_lh=LocalHighTone.PREV, tonicity=tonicity
    )
    valid_blocked = [
        str(uf)
        for uf in candidates_blocked
        if check_prediction(
            str(uf),
            surface,
            initial_lh=LocalHighTone.PREV,
            tonicity=tonicity,
        )
    ]

    found_blocked_match = False
    for uf in valid_blocked:
        if uf.endswith(expected_ending):
            found_blocked_match = True
            break

    if found_blocked_match:
        print(
            f"      [DIAGNOSIS] Matches expected ending '{expected_ending}' IF we assume 'BLOCKED' environment (Preceding High Tone)."
        )
        return

    if not valid_candidates and not found_blocked_match:
        print(
            "      [DIAGNOSIS] No valid underlying forms found even with BLOCKED check."
        )


def analyze_class_coverage(verbs_with_forms):
    print("\n--- Class Coverage Analysis ---")

    # Load underlying class definitions
    class_defs = {}
    # Assuming running from repo root
    underlying_classes_path = "data/classes_underlying.csv"
    if not os.path.exists(underlying_classes_path):
        print(f"File not found: {underlying_classes_path}")
        return

    with open(underlying_classes_path, "r") as f:
        reader = DictReader(f)
        for row in reader:
            class_defs[row["class"]] = row

    target_class = "go"
    if target_class not in class_defs:
        print(f"Class '{target_class}' not found in {underlying_classes_path}")
        return

    target_def = class_defs[target_class]

    # Filter for verbs of the target class
    class_verbs = [
        (v, row) for v, row in verbs_with_forms if v.class_name == target_class
    ]

    total_verbs = len(class_verbs)
    if total_verbs == 0:
        print(f"No verbs found for class '{target_class}'")
        return

    print(f"Analyzing {total_verbs} verbs of class '{target_class}'")

    # Forms to check (intersection of FORMS and columns in CSV)
    forms_to_check = [
        f
        for f in ["present", "imperfective", "perfective", "imperative", "infinitive"]
        if f in target_def and target_def[f].strip()
    ]

    for form_name in forms_to_check:
        # Get target endings
        raw_endings = target_def[form_name]
        target_endings = [e.strip() for e in raw_endings.split(";") if e.strip()]

        if not target_endings:
            continue

        print(f"\nForm: {form_name}")

        for ending in target_endings:
            match_count = 0
            valid_verbs_for_form = 0

            for verb, row in class_verbs:
                surface = row.get(form_name)
                if not surface:
                    continue

                valid_verbs_for_form += 1

                # Generate underlying forms
                tonicity = get_tonicity_for_form(verb, form_name)
                underlying_candidates = generate_underlying_forms(
                    surface, tonicity=tonicity
                )

                # Check if ANY valid underlying form ends with the target ending
                matches_ending = False
                for uf in underlying_candidates:
                    # Check if candidate is valid (reconstructs surface)
                    if not check_prediction(str(uf), surface, tonicity=tonicity):
                        continue

                    # Check ending match
                    # We use str(uf) which is the string representation of LexedForm
                    if str(uf).endswith(ending):
                        matches_ending = True
                        break

                if matches_ending:
                    match_count += 1
                else:
                    diagnose_mismatch(verb, surface, ending, tonicity=tonicity)

            if valid_verbs_for_form > 0:

                percentage = (match_count / valid_verbs_for_form) * 100
                print(
                    f"  Ending '{ending}': {match_count}/{valid_verbs_for_form} ({percentage:.1f}%)"
                )
            else:
                print(f"  Ending '{ending}': No valid surface forms found.")


def main():
    verbs, cnd_corpus, corpus_id_to_entries = load_data()

    # Get eligible verbs and their surface stems
    verbs_with_forms = write_elligible_verbs(verbs, cnd_corpus, corpus_id_to_entries)

    output_rows = []
    for verb, row in verbs_with_forms:
        corpus_id = row["corpus_id"]
        for fn in FORMS:
            surface_stem = row.get(fn)
            if not surface_stem:
                continue
            tonicity = get_tonicity_for_form(verb, fn)
            underlying_candidates = generate_underlying_forms(
                surface_stem, tonicity=tonicity
            )
            for uf in underlying_candidates:
                if check_prediction(str(uf), surface_stem, tonicity=tonicity):
                    output_rows.append(
                        {
                            "corpus_id": corpus_id,
                            "definition": verb.definition,
                            "class": verb.class_name,
                            "form": fn,
                            "surface_stem": surface_stem,
                            "underlying_stem": str(uf),
                        }
                    )

    if output_rows:
        with open(underlying_stems_path, "w", newline="") as f:
            writer = DictWriter(
                f,
                fieldnames=[
                    "corpus_id",
                    "definition",
                    "class",
                    "form",
                    "surface_stem",
                    "underlying_stem",
                ],
            )
            writer.writeheader()
            writer.writerows(output_rows)
        print(f"Underlying stems written to {underlying_stems_path}")

    # Analyze class coverage for "go" class
    analyze_class_coverage(verbs_with_forms)

    # Verification of a few entries
    if verbs_with_forms and False:
        print("\nVerification of a few eligible verbs:")
        for verb, row in verbs_with_forms[:5]:
            print(f"\nVerb: {verb.definition} (Root: {verb.h_grade_root})")
            for fn in ["present", "perfective"]:
                surface = row.get(fn)
                if not surface:
                    continue

                # Generate underlying forms
                tonicity = get_tonicity_for_form(
                    verb, fn
                )  # Changed from form_name to fn
                underlying_candidates = generate_underlying_forms(
                    surface, tonicity=tonicity
                )
                print(f"  Form: {fn:12} Surface: {surface:15}")
                for i, uf in enumerate(
                    underlying_candidates[:2]
                ):  # Show first 2 candidates
                    reconstructed = infer_surface_forms(uf, tonicity=tonicity)
                    target_mask = strip_morpheme_boundaries(surface)
                    match = any(
                        target_mask == strip_morpheme_boundaries(r)
                        for r in reconstructed
                    )
                    print(
                        f"    Candidate {i+1}: {str(uf):15} | Reconstructed: {reconstructed[0][:20]}... | Match: {match}"
                    )
                if len(underlying_candidates) > 2:
                    print(f"    ({len(underlying_candidates)-2} more candidates...)")


if __name__ == "__main__":
    main()
