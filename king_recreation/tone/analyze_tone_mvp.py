import io
import itertools
import json
import os
from csv import DictReader, DictWriter
from dataclasses import dataclass
from enum import Enum
from typing import List, Union

from king_recreation.paths import (
    cherokee_nation_dictionary_path,
    corpus_to_cnd_path,
    reconstructable_verbs_path,
    stems_with_tone_corpus_path,
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


def tone_sequence_from_corpus_form(s: str) -> List[Union[Consonant, Vowel]]:
    if not s:
        return []

    res = []
    idx = 0
    while idx < len(s):
        char = s[idx]

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
                    idx_start=idx,
                    idx_end=tone_end - 1,
                )
            )
            idx = tone_end
        else:
            # Consonant or glottal stop
            res.append(Consonant(value=char, idx_start=idx, idx_end=idx))
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


class Environment(Enum):
    SPREAD = "spread"
    NO_SPREAD = "no_spread"
    BLOCKED = "blocked"

    @staticmethod
    def from_state(lh: LocalHighTone, prev_long: bool) -> "Environment":
        if lh == lh.PREV:
            return Environment.BLOCKED
        elif not prev_long or lh == lh.TWO_PREV:
            return Environment.NO_SPREAD
        else:
            return Environment.SPREAD if prev_long else Environment.NO_SPREAD


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

    def __str__(self):
        v = self.quality * (2 if self.length else 1)
        if self.glottal_position in [GlottalPosition.PRE_C, GlottalPosition.NO_C]:
            return v + "'"
        return v


@dataclass(frozen=True)
class LexedForm:
    tokens: List[Union[HistoricalVowel, Consonant]]

    def __str__(self):
        res = []
        pending_post_c = False
        for i, token in enumerate(self.tokens):
            if isinstance(token, Consonant):
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
                        if s[k] not in VOWEL_SET and s[k] != "'":
                            has_following_c = True
                            break
                    g_pos = (
                        GlottalPosition.PRE_C
                        if has_following_c
                        else GlottalPosition.NO_C
                    )
                    idx += 1
                tokens.append(HistoricalVowel(quality, length, g_pos))
            else:
                # Consonant or glottal
                tokens.append(Consonant(char, idx, idx))
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
        [VowelTone.hh, Consonant("'", -1, -1)],
        [VowelTone.lh, VowelTone.h, Consonant("'", -1, -1)],
    ],
    H1Config(True, GlottalPosition.NO_C, Environment.NO_SPREAD): [
        [VowelTone.hh, Consonant("'", -1, -1)]
    ],
    H1Config(True, GlottalPosition.NO_C, Environment.BLOCKED): [
        [VowelTone.l, Consonant("'", -1, -1)]
    ],
    # Short NO_C
    H1Config(False, GlottalPosition.NO_C, Environment.SPREAD): [
        [VowelTone.lh, VowelTone.h, Consonant("'", -1, -1)]
    ],
    H1Config(False, GlottalPosition.NO_C, Environment.NO_SPREAD): [
        [VowelTone.h, Consonant("'", -1, -1)]
    ],
    H1Config(False, GlottalPosition.NO_C, Environment.BLOCKED): [
        [VowelTone.l, Consonant("'", -1, -1)]
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
        [VowelTone.h, Consonant("'", -1, -1)],
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


def predict_h1_for_form(form_str: str) -> List[tuple[Vowel, List[H1Config]]]:
    """
    Core logic to predict possible H1 configurations for a single form string.
    """
    if not form_str:
        return []

    # Strip morpheme boundaries before parsing
    clean_form = strip_morpheme_boundaries(form_str)
    tone_sequence = tone_sequence_from_corpus_form(clean_form)
    local_high = LocalHighTone.NONE
    prev_long = False
    prev_tone = None

    results = []

    for i, seg in enumerate(tone_sequence):
        if isinstance(seg, Vowel):
            h1_found = False
            # Check if this vowel or the following consonant is a glottal stop candidate
            has_glottal = False
            if i + 1 < len(tone_sequence):
                next_seg = tone_sequence[i + 1]
                if isinstance(next_seg, Consonant) and next_seg.value == "'":
                    has_glottal = True

            has_following_c = False
            # Check for any consonant following this vowel (possibly after a glottal stop)
            for j in range(i + 1, len(tone_sequence)):
                next_seg = tone_sequence[j]
                if isinstance(next_seg, Consonant):
                    if next_seg.value != "'":
                        has_following_c = True
                        break
                elif isinstance(next_seg, Vowel):
                    # Hit next vowel, no consonant in between (except maybe glottal)
                    break

            # We only look for H1 if we see a candidate tone (H, HH, or HL)
            # or if a glottal stop is explicitly present.
            if has_glottal or seg.tone in [
                VowelTone.hh,
                VowelTone.h,
                VowelTone.hl,
                VowelTone.lf,
                VowelTone.lh,
            ]:
                env = Environment.from_state(local_high, prev_long)
                possible_positions = get_possible_glottal_positions(
                    env, seg.tone, prev_tone, has_glottal, has_following_c
                )
                if possible_positions:
                    results.append((seg, possible_positions))
                    h1_found = True

            # update flags for next syllable
            if h1_found:
                local_high = LocalHighTone.PREV
            else:
                local_high = local_high.advance()

            if seg.tone:
                prev_long = len(seg.tone.value) == 2
                prev_tone = seg.tone
            else:
                prev_long = False
                prev_tone = None

    return results


def generate_underlying_forms(form_str: str) -> List[LexedForm]:
    """
    Generate all possible underlying form objects (LexedForm) from a surface form string.
    """
    if not form_str:
        return []

    clean_form = strip_morpheme_boundaries(form_str)
    tone_sequence = tone_sequence_from_corpus_form(clean_form)
    local_high = LocalHighTone.NONE
    prev_long = False
    prev_tone = None

    # Path state: (tokens, lh, pl, pt, skip_surface_glottal)
    initial_path = ([], local_high, prev_long, prev_tone, False)
    paths = [initial_path]

    for i, seg in enumerate(tone_sequence):
        new_paths = []
        for tokens, lh, pl, pt, skip_surface_glottal in paths:
            if isinstance(seg, Consonant):
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

                env = Environment.from_state(lh, pl)
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

                if configs:
                    for cfg in configs:
                        hv = HistoricalVowel(
                            seg.quality, cfg.historically_long, cfg.glottal_position
                        )
                        new_paths.append(
                            (
                                tokens + [hv],
                                LocalHighTone.PREV,
                                len(seg.tone.value) == 2 if seg.tone else False,
                                seg.tone,
                                has_glottal,  # We skip following glottal if inferred H1
                            )
                        )
                else:
                    # Plain vowel
                    is_long = seg.tone and len(seg.tone.value) == 2
                    hv = HistoricalVowel(seg.quality, is_long, None)
                    new_paths.append(
                        (
                            tokens + [hv],
                            lh.advance(),
                            is_long,
                            seg.tone,
                            False,
                        )
                    )
        paths = new_paths

    return [LexedForm(p[0]) for p in paths]


def predict_underlying_form(verb, forms, form_name):
    # Determine the tone sequence for the given form
    form_str = forms[form_name]
    return generate_underlying_forms(form_str)


def infer_surface_forms(lexed: Union[LexedForm, str]) -> List[str]:
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
                else:
                    res.append(surface_tones[k])
            return ["".join(res)]

        token = tokens[u_idx]
        if isinstance(token, Consonant):
            return solve(u_idx + 1, local_high, prev_long, surface_tones)

        # It's a HistoricalVowel
        g_pos = token.glottal_position
        results = []
        if g_pos:
            env = Environment.from_state(local_high, prev_long)
            cfg = H1Config(token.length, g_pos, env)
            sequences = H1_INFERENCES.get(cfg, [])
            if sequences:
                for seq in sequences:
                    new_tones = list(surface_tones)
                    v_tones = [item for item in seq if isinstance(item, VowelTone)]
                    c_inline = [
                        item.value for item in seq if isinstance(item, Consonant)
                    ]

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
                # No rule: Fallback to Low
                new_tones = list(surface_tones)
                if new_tones[u_idx] is None:
                    new_tones[u_idx] = token.quality + ("22" if token.length else "2")
                results.extend(
                    solve(u_idx + 1, local_high.advance(), token.length, new_tones)
                )
        else:
            # Plain vowel
            new_tones = list(surface_tones)
            if new_tones[u_idx] is None:
                new_tones[u_idx] = token.quality + ("22" if token.length else "2")
            results.extend(
                solve(u_idx + 1, local_high.advance(), token.length, new_tones)
            )

        return results

    return solve(0, LocalHighTone.NONE, False, [None] * len(tokens))


def check_prediction(underlying_form: str, target_surface: str) -> bool:
    """
    Integrity check: Can this underlying form generate the target surface form?
    """
    # Normalize clean_target by parsing and re-serializing to ensure consistent tone representation
    clean_target = strip_morpheme_boundaries(target_surface)
    seq = tone_sequence_from_corpus_form(clean_target)
    normalized_target = "".join(str(s) for s in seq)

    surface_candidates = infer_surface_forms(underlying_form)
    return normalized_target in surface_candidates


def main():
    verbs, cnd_corpus, corpus_id_to_entries = load_data()

    verbs_with_forms = write_elligible_verbs(verbs, cnd_corpus, corpus_id_to_entries)

    forms_to_analyze = ["present", "imperfective", "perfective"]

    print("\nVerification of a few eligible verbs:")
    for verb, row in verbs_with_forms[:5]:
        print(f"\nVerb: {verb.definition} (Root: {verb.h_grade_root})")
        for fn in ["present", "perfective"]:
            surface = row.get(fn)
            if not surface:
                continue

            underlying_candidates = generate_underlying_forms(surface)
            print(f"  Form: {fn:12} Surface: {surface:15}")
            for i, uf in enumerate(
                underlying_candidates[:2]
            ):  # Show first 2 candidates
                reconstructed = infer_surface_forms(uf)
                match = any(
                    strip_morpheme_boundaries(surface) in r for r in reconstructed
                )
                print(
                    f"    Candidate {i+1}: {str(uf):15} | Reconstructed: {reconstructed[0][:20]}... | Match: {match}"
                )
            if len(underlying_candidates) > 2:
                print(f"    ({len(underlying_candidates)-2} more candidates...)")


if __name__ == "__main__":
    main()
