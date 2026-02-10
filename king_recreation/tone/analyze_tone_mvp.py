import io
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
            writer = DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows([row for _verb, row in rows])
        print(f"Saved {len(rows)} rows to {stems_with_tone_corpus_path}")

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


# named tuple?
@dataclass(frozen=True)
class H1Config:
    historically_long: bool
    glottal_position: GlottalPosition
    env: Environment


# to be populated from docs/tone_mvp.md
H1_INFERENCES = {
    # Long PRE_C
    H1Config(True, GlottalPosition.PRE_C, Environment.SPREAD): [
        [VowelTone.lh, VowelTone.hl]
    ],
    H1Config(True, GlottalPosition.PRE_C, Environment.NO_SPREAD): [[VowelTone.hh]],
    H1Config(True, GlottalPosition.PRE_C, Environment.BLOCKED): [[VowelTone.lf]],
    # Short PRE_C
    H1Config(False, GlottalPosition.PRE_C, Environment.SPREAD): [
        [VowelTone.lh, VowelTone.hl]
    ],
    H1Config(False, GlottalPosition.PRE_C, Environment.NO_SPREAD): [[VowelTone.hl]],
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
                # Sequence match: current tone must match last, previous tone should match first (if known)
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


def predict_underlying_form(verb, forms, form_name):
    # Determine the tone sequence for the given form
    form_str = forms[form_name]
    return predict_h1_for_form(form_str)


def main():
    verbs, cnd_corpus, corpus_id_to_entries = load_data()

    verbs_with_forms = write_elligible_verbs(verbs, cnd_corpus, corpus_id_to_entries)

    forms_to_analyze = ["present", "imperfective", "perfective"]

    for verb, forms in verbs_with_forms:
        opts_per_form = {}
        for fn in forms_to_analyze:
            underlying_opts = predict_underlying_form(verb, forms, fn)
            opts_per_form[fn] = underlying_opts

        # find common derivations
    #     # PLAN:
    #     # window scan along, looking for high tones (3, 32, 33)
    #     # check for preceeding 23-, spread ability, etc. as we scan
    #     # prev_long, last_high both start at None
    #     # window cond turn into spread conn
    #     # Blocked, No spread, Spread
    #     # Table lookup of high tone (3, 32, 33) gives possible positions for glottal
    #     #

    #     # print(f"{verb.definition} | {form_name} | Stem Tones: {stem_tones}")
    #     # --- END MVP ANALYSIS LOGIC ---

    print(
        f"\nScaffold complete. Processed {len(verbs)} verbs, {eligible_count} were eligible for analysis."
    )


if __name__ == "__main__":
    main()
