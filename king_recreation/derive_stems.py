import csv
import os
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple

from king_recreation.h_alternation import grades_are_compatible
from king_recreation.morphemes.middle_voice import MiddleVoice
from king_recreation.morphemes.post_root_morphemes import match_post_root_morphemes
from king_recreation.morphemes.prepronominals import PrePronominalConfig
from king_recreation.morphemes.pronominals import (
    MetathesisStrategy,
    PronominalConfig,
    StemType,
    detach_prefix,
    use_glottal_grade,
)
from king_recreation.paths import (
    corpus_no_asp_path,
    corpus_no_pre_no_asp_path,
    corpus_path,
    pre_parsing_failures_path,
)


@dataclass
class Derivation:
    pre_config: PrePronominalConfig
    pron_config: PronominalConfig
    h_grade: str
    g_grade: Optional[str]
    stems: Dict[str, str]  # form_name -> stripped_stem (pronominal base)
    metathesis_involved: bool = False

    def to_row(self):
        row = {}

        for fn, stem in self.stems.items():
            row[fn] = stem

        row["h_grade"] = self.h_grade
        row["g_grade"] = self.g_grade
        row["metathesis_involved"] = str(self.metathesis_involved)
        row.update(**self.pron_config.to_row())
        row.update(**self.pre_config.to_row())

        return row


def is_strict_compatible(s1: str, s2: str) -> bool:
    if s1 == s2:
        return True
    if s1.startswith(s2) or s2.startswith(s1):
        return True
    common_len = 0
    for c1, c2 in zip(s1, s2):
        if c1 == c2:
            common_len += 1
        else:
            break
    return common_len >= 3 or common_len == min(len(s1), len(s2))


def strip_prepronominals(
    forms: Dict[str, str], config: PrePronominalConfig
) -> Optional[Dict[str, str]]:
    stripped = {}
    for fn, word in forms.items():
        current = word
        if config.translocutive or (fn == "imperative" and config.translocutiveImpOnly):
            if current.startswith("wi"):
                current = current[2:]
            elif current.startswith("w"):
                current = current[1:]
            elif current.startswith("hw"):
                current = "h" + current[2:]
            else:
                return None
        if config.partitive:
            if fn == "infinitive":
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
                    return None
        if config.distributive:
            if fn == "infinitive" or (
                fn == "imperative" and not config.distributiveImpIsFutProg
            ):
                if current.startswith("ts"):
                    current = current[2:]
                elif current.startswith("ti"):
                    current = current[2:]
                elif current.startswith("t"):
                    current = current[1:]
                else:
                    return None
            else:
                if current.startswith("te"):
                    current = current[2:]
                elif current.startswith("t"):
                    current = current[1:]
                else:
                    return None
        stripped[fn] = current
    return stripped


def derive_pronominals(
    intermediate_forms: Dict[str, str], pron_config: PronominalConfig, log=False
) -> Optional[Derivation]:

    derived_stems = {}
    metathesis_used = False
    for fn, word in intermediate_forms.items():
        stem, fn_metathesis_used = detach_prefix(word, fn, pron_config)
        metathesis_used = metathesis_used or fn_metathesis_used
        if stem is None:
            return None

        derived_stems[fn] = stem
    res = stems_are_consistent(derived_stems, pron_config, log=log)
    if res is not None:
        h_grade, g_grade = res
        # Metathesis must be used if strategy is not none
        if pron_config.stem_type.is_valid_for_stem(h_grade) and (
            not metathesis_used
            == (pron_config.metathesis_strategy == MetathesisStrategy.NONE)
        ):
            return Derivation(
                pre_config=None,
                pron_config=pron_config,
                h_grade=h_grade,
                g_grade=g_grade,
                stems=derived_stems,
                metathesis_involved=metathesis_used,
            )
        else:
            return None
    else:
        return None


def derive_middle(der: Derivation) -> List[Derivation]:
    der_dict = asdict(der)
    der_dict["pre_config"] = PrePronominalConfig(**der_dict["pre_config"])
    pron_dict = asdict(der.pron_config)
    options = []
    for middle_voice, (h_grade, g_grade) in MiddleVoice.identify_middle_voice(
        der.h_grade, der.g_grade
    ):
        der_dict["h_grade"] = h_grade
        der_dict["g_grade"] = g_grade

        der_dict["stems"] = {
            fn: middle_voice.try_strip_form(form) if form else None
            for fn, form in der.stems.items()
        }

        pron_dict["middle_voice"] = middle_voice
        der_dict["pron_config"] = PronominalConfig(**pron_dict)
        options.append(
            Derivation(
                **der_dict,
            )
        )
    return options


def stems_are_consistent(
    derived_stems: dict[str, str], pron_config: PronominalConfig, log=False
) -> Optional[Tuple[str, str]]:
    """
    Check if a set of derived stems are consistent.

    1. Check that h-grade stems are consistent (using is_strict_compatible)
    2. Check that glottal grade stems are consistent (using is_loose_compatible)
    3. Check that h and glottal grade stems match each other up to h alternation

    log: If True, prints detailed step-by-step validation logic.
    """
    if log:
        print("")
    h_candidate = derived_stems.get("present")
    g_candidate = derived_stems.get("present_1sg")

    if h_candidate is None:
        print(derived_stems)
        return None

    # check that h and g grades are consistent within grades
    passing = True
    for fn, s in derived_stems.items():
        if use_glottal_grade(fn, pron_config) and g_candidate is not None:
            check = is_strict_compatible(s, g_candidate)
            passing &= check
            if log:
                print("g grade, loose", fn, s, g_candidate, check)
        else:
            check = False
            # HOW DOES is strict compatible change this?

            if fn == "present":
                # The primary h-grade stem is derived from 'present' (3rd present).
                check = is_strict_compatible(s, h_candidate)
                if log:
                    print("h grade, strict", fn, s, h_candidate, check)
            else:
                # Other h-grade forms must also be strictly compatible with the h-candidate.
                check = is_strict_compatible(s, h_candidate)
                if log:
                    print("h grade, loose", fn, s, h_candidate, check)

            passing &= check

    if not passing:
        return None

    # check that grades are consistent together
    if g_candidate and not grades_are_compatible(h=h_candidate, glottal=g_candidate):
        return None

    return h_candidate, g_candidate


def iter_pre_configs(forms):
    """
    Iterate over valid pre-configs
    """
    for t in [False, True]:
        t2_opts = [False] if t else [False, True]
        for t2 in t2_opts:
            for p in [False, True]:
                for d in [False, True]:
                    d2_opts = [False, True] if d else [False]
                    for d2 in d2_opts:
                        pre_config = PrePronominalConfig(t, t2, p, d, d2)
                        intermediate = strip_prepronominals(forms, pre_config)
                        if intermediate is None:
                            continue
                        else:
                            yield pre_config, intermediate


class StemDeriver:
    def derive_row(
        self, row: Dict[str, str], ref: Dict[str, str] = None
    ) -> List[Derivation]:
        form_names = [
            "present",
            "present_1sg",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]
        if ref:
            forms = {fn: row[fn] for fn in form_names if ref.get(fn)}
        else:
            forms = {fn: row[fn] for fn in form_names if row.get(fn)}
        if not forms:
            return []

        valid_derivations: list[Derivation] = []

        for pre_config, intermediate in iter_pre_configs(forms):
            set_type = "b" if intermediate["present"].startswith("u") else "a"
            ka = intermediate["present"].startswith("k")
            aki = intermediate.get("present_1sg", "").startswith("aki")
            b3sg_starts_uwa = next(
                (
                    intermediate.get(fn, "").startswith("uwa")
                    for fn in (["present", "completive", "infinitive"])
                    if intermediate.get(fn, "").startswith("u")
                ),
                None,
            )
            long_start_options = (
                [b3sg_starts_uwa] if b3sg_starts_uwa is not None else [False, True]
            )
            for plural in [False, True]:
                for use_3rd in [False, True]:
                    for meta in MetathesisStrategy:
                        for s_type in StemType:
                            uwa_opts = [False]
                            if s_type == StemType.VOWEL_V:
                                uwa_opts = (
                                    [b3sg_starts_uwa]
                                    if b3sg_starts_uwa is None
                                    else [False, True]
                                )
                            for uwa in uwa_opts:
                                for long_start in long_start_options:
                                    pron_config = PronominalConfig(
                                        set_type=set_type,
                                        stem_type=s_type,
                                        metathesis_strategy=meta,
                                        plural_pronouns=plural,
                                        use_ka_variant=ka,
                                        long_start=long_start,
                                        uwa_replaces_v=uwa,
                                        use_aki_for_1st_set_b=aki,
                                        use_3rd_person_object=use_3rd,
                                    )
                                    res = derive_pronominals(
                                        intermediate,
                                        pron_config,
                                        # log="calling" in row["definition"],
                                    )
                                    if res:
                                        res.pre_config = pre_config
                                        valid_derivations.extend(derive_middle(res))
        if not valid_derivations:
            return []

        valid_derivations.sort(
            key=lambda d: (
                d.pron_config.use_3rd_person_object,
                d.pron_config.metathesis_strategy != MetathesisStrategy.NONE,
                d.pron_config.use_ka_variant,
                sum(
                    [
                        d.pre_config.translocutive,
                        d.pre_config.partitive,
                        d.pre_config.distributive,
                    ]
                ),
            )
        )
        return valid_derivations


def main():
    full_corpus = {}
    with open(corpus_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            full_corpus[r["corpus_id"]] = r

    deriver = StemDeriver()
    labeled_data = []
    failures = []
    with open(corpus_no_asp_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ref = full_corpus.get(row["corpus_id"])
            derivations = deriver.derive_row(row, ref)
            if not derivations:
                failures.append(row)
            else:
                # d = derivations[0]
                for d in derivations:
                    # copy row
                    stripped_row = {**row, **d.to_row()}
                    # labeled_data.append({**d.to_row()})
                    labeled_data.extend(match_post_root_morphemes(stripped_row))

    form_names = [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]

    if labeled_data:
        keys = labeled_data[0].keys()
        keys = [k for k in keys if k not in form_names]
        with open(corpus_no_pre_no_asp_path, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(
                {k: v for k, v in row.items() if k in keys} for row in labeled_data
            )
    if failures:
        keys = failures[0].keys()
        with open(pre_parsing_failures_path, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(failures)
    print(f"Processed {len(labeled_data) + len(failures)} rows.")
    print(f"Success: {len(labeled_data)}")
    print(f"Failures: {len(failures)}")


if __name__ == "__main__":
    main()
