from morphology.morphemes.prefixes.prepronominals import PrePronominalConfig
from morphology.morphemes.prefixes.pronominals import PronominalConfig, StemType
from morphology.morphology_types import Aspect, Number, Person, PronominalSet
from morphology.word_spec import SyntacticCategory, WordSpec


def derive_pronouns(
    examples: list[tuple[str, WordSpec]],
) -> list[tuple[PrePronominalConfig, PronominalConfig]]:
    """
    Given a list of (word, WordSpec) tuples, identifies all compatible prefix configurations
    (PrePronominalConfig and PronominalConfig).
    """
    # 1. Collect candidate attributes from the WordSpec elements to strip prepronominals
    # We need to find prepronominal configurations that successfully strip prefix characters for all examples.
    valid_configs = []

    # We iterate over all possible prepronominal config combinations
    for t in [False, True]:
        t2_opts = [False] if t else [False, True]
        for t2 in t2_opts:
            for p in [False, True]:
                for d in [False, True]:
                    pre_config = PrePronominalConfig(
                        translocutive=t,
                        translocutiveImpOnly=t2,
                        partitive=p,
                        distributive=d,
                    )

                    # Try stripping on all examples
                    intermediate: list[str] = []
                    possible = True
                    for word, spec in examples:
                        current = word
                        # translocutive check
                        if pre_config.translocutive or (
                            spec.aspect == Aspect.IMPERATIVE
                            and pre_config.translocutiveImpOnly
                        ):
                            if current.startswith("wi"):
                                current = current[2:]
                            elif current.startswith("w"):
                                current = current[1:]
                            elif current.startswith("hw"):
                                current = "h" + current[2:]
                            else:
                                possible = False
                                break

                        # partitive check
                        if pre_config.partitive:
                            if spec.syntactic_category == SyntacticCategory.NOMINAL:
                                if current.startswith("iy"):
                                    current = current[2:]
                                elif current.startswith("i"):
                                    current = current[1:]
                            else:
                                if current.startswith("ni"):
                                    current = current[2:]
                                elif current.startswith("n"):
                                    current = current[1:]
                                elif current.startswith("hn"):
                                    current = "h" + current[2:]
                                elif current.startswith("i"):
                                    pass
                                else:
                                    possible = False
                                    break

                        # distributive check
                        if pre_config.distributive:
                            if (
                                spec.syntactic_category == SyntacticCategory.NOMINAL
                                or (
                                    spec.aspect == Aspect.IMPERATIVE
                                    and not spec.stative
                                )
                            ):
                                if current.startswith("ts"):
                                    current = current[2:]
                                elif current.startswith("ti"):
                                    current = current[2:]
                                elif current.startswith("t"):
                                    current = current[1:]
                                else:
                                    possible = False
                                    break
                            else:
                                if current.startswith("te"):
                                    current = current[2:]
                                elif current.startswith("t"):
                                    current = current[1:]
                                else:
                                    possible = False
                                    break
                        intermediate.append(current)

                    if not possible:
                        continue

                    # 2. Under this pre_config, analyze the intermediate words to determine pronominal config variables.
                    # Find a 'candidate 3rd person +allow_set_a form' where spec.person == Person.THIRD,
                    # spec.number == Number.SINGULAR, and spec.aspect not in (Aspect.PERFECTIVE, Aspect.INFINITIVE).
                    candidate_3rd_set_a = None
                    for idx, (word, spec) in enumerate(examples):
                        if (
                            spec.person == Person.THIRD
                            and spec.number == Number.SINGULAR
                            and spec.aspect
                            not in (Aspect.PERFECTIVE, Aspect.INFINITIVE)
                        ):
                            candidate_3rd_set_a = intermediate[idx]
                            break

                    if candidate_3rd_set_a is not None:
                        set_types = [
                            (
                                PronominalSet.SET_B
                                if candidate_3rd_set_a.startswith("u")
                                else PronominalSet.SET_A
                            )
                        ]
                        ka = candidate_3rd_set_a.startswith("k")
                    else:
                        set_types = [PronominalSet.SET_A, PronominalSet.SET_B]
                        ka = any(w.startswith("k") for w in intermediate)

                    # Find a '1st person +allow_set_a' form where spec.person == Person.FIRST,
                    # spec.number == Number.SINGULAR, and spec.aspect not in (Aspect.PERFECTIVE, Aspect.INFINITIVE).
                    candidate_1st_set_a = None
                    for idx, (word, spec) in enumerate(examples):
                        if (
                            spec.person == Person.FIRST
                            and spec.number == Number.SINGULAR
                            and spec.aspect
                            not in (Aspect.PERFECTIVE, Aspect.INFINITIVE)
                        ):
                            candidate_1st_set_a = intermediate[idx]
                            break

                    if candidate_1st_set_a is not None:
                        aki = candidate_1st_set_a.startswith(
                            "aki"
                        ) or candidate_1st_set_a.startswith("akhi")
                    else:
                        aki = False

                    b3sg_starts_uwa = None
                    for idx, (word, spec) in enumerate(examples):
                        if (
                            spec.person == Person.THIRD
                            and spec.number == Number.SINGULAR
                            and (
                                spec.aspect in (Aspect.PRESENT, Aspect.INFINITIVE)
                                or (
                                    spec.aspect == Aspect.PERFECTIVE
                                    and spec.syntactic_category
                                    == SyntacticCategory.NOMINAL
                                )
                            )
                        ):
                            w_val = intermediate[idx]
                            if w_val.startswith("u"):
                                b3sg_starts_uwa = w_val.startswith("uwa")
                                break

                    for set_type in set_types:
                        for plural in [False, True]:
                            for use_3rd in [False, True]:
                                for s_type in StemType:
                                    for allow_h_metathesis in [False, True]:
                                        uwa_opts = [False]
                                        if s_type == StemType.VOWEL_V:
                                            if b3sg_starts_uwa is None:
                                                uwa_opts = [False, True]
                                            else:
                                                uwa_opts = [b3sg_starts_uwa]
                                        for uwa in uwa_opts:
                                            pron_config = PronominalConfig(
                                                set_type=set_type,
                                                stem_type=s_type,
                                                allow_h_metathesis=allow_h_metathesis,
                                                plural_pronouns=plural,
                                                use_ka_variant=ka,
                                                uwa_replaces_v=bool(uwa),
                                                use_aki_for_1st_set_b=aki,
                                                use_3rd_person_object=use_3rd,
                                            )
                                            valid_configs.append(
                                                (pre_config, pron_config)
                                            )

    return valid_configs
