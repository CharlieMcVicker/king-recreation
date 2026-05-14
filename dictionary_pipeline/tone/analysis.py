from typing import cast

from dictionary_pipeline.dictionary_forms import DictionaryVerb
from dictionary_pipeline.tone.models import (
    Environment,
    GlottalPosition,
    H1Config,
    HistoricalVowel,
    LexedForm,
    LocalHighTone,
    MorphemeBoundary,
    Tonicity,
    tone_sequence_from_corpus_form,
)
from dictionary_pipeline.tone.utils import (
    Consonant,
    Vowel,
    VowelTone,
    strip_morpheme_boundaries,
)


def get_tonicity_for_form(verb: DictionaryVerb, form_name: str) -> Tonicity:
    """Determine the tonicity for a given verb form."""
    if form_name == "infinitive":
        return Tonicity.INFINITIVE

    if form_name == "imperative" and not verb.morphology.config.stative:
        pre = verb.morphology.config.pre
        has_pre = (
            pre.translocutive
            or pre.translocutiveImpOnly
            or pre.partitive
            or pre.distributive
        )
        if not has_pre:
            return Tonicity.ATONIC

    return Tonicity.TONIC


# to be populated from docs/tone_mvp.md
H1_INFERENCES: dict[H1Config, list[list[VowelTone | Consonant]]] = {
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
    prev_tone: VowelTone | None = None,
    has_glottal: bool = False,
    has_following_c: bool = False,
) -> list[H1Config]:
    """
    Search H1_INFERENCES for underlying configurations that could produce the observed tone.
    """
    results: list[H1Config] = []
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


def generate_underlying_forms(
    form_str: str,
    initial_lh: LocalHighTone = LocalHighTone.NONE,
    initial_pl: bool = False,
    tonicity: Tonicity = Tonicity.TONIC,
) -> list[LexedForm]:
    """
    Generate all possible underlying form objects (LexedForm) from a surface form string.
    """
    if not form_str:
        return []

    # Use form_str directly to preserve boundaries if any
    tone_sequence = tone_sequence_from_corpus_form(form_str)
    prev_tone = None

    # Path state: (tokens, lh, pl, pt, skip_surface_glottal)
    initial_path: tuple[
        list[HistoricalVowel | Consonant | MorphemeBoundary],
        LocalHighTone,
        bool,
        VowelTone | None,
        bool,
    ] = ([], initial_lh, initial_pl, prev_tone, False)
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
                            v = cast(Vowel, tone_sequence[k])
                            if v.tone:
                                next_v_long = len(v.tone.value) == 2
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


def predict_h1_for_form(
    form_str: str, tonicity: Tonicity = Tonicity.TONIC
) -> list[tuple[Vowel, list[H1Config]]]:
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


def infer_surface_forms(
    lexed: "LexedForm | str",
    initial_lh: LocalHighTone = LocalHighTone.NONE,
    tonicity: Tonicity = Tonicity.TONIC,
) -> list[str]:
    """
    Forward inference: Generate possible surface forms from a LexedForm (or string).
    """
    if isinstance(lexed, str):
        lexed = LexedForm.from_str(lexed)

    tokens = lexed.tokens

    def solve(
        u_idx: int,
        local_high: LocalHighTone,
        prev_long: bool,
        surface_tones: list[str | None],
    ) -> list[str]:
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
            is_next_long = cast(HistoricalVowel, next_v).length if next_v else False

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
                                    cast(HistoricalVowel, tokens[prev_v_idx]).quality
                                    + v_tones[0].value
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
                                    cast(HistoricalVowel, tokens[prev_v_idx]).quality
                                    + v_tones[0].value
                                )

                    results.extend(
                        solve(u_idx + 1, LocalHighTone.PREV, token.length, new_tones)
                    )
            else:
                # No H1 rule, but what if H2 is present?
                if h2:
                    new_tones = list(surface_tones)
                    new_tones[u_idx] = token.quality + (
                        h2_tone_enum.value if h2_tone_enum else ""
                    )
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
                new_tones[u_idx] = token.quality + (
                    h2_tone_enum.value if h2_tone_enum else ""
                )

            next_lh = LocalHighTone.PREV if h2_blocks else local_high.advance()
            results.extend(solve(u_idx + 1, next_lh, token.length, new_tones))
        else:
            # Plain vowel
            env = Environment.from_state(local_high, prev_long, tonicity)
            new_tones = list(surface_tones)
            next_lh = local_high.advance()
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
