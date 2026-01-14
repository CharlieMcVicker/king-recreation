import os
import csv
from dataclasses import dataclass, asdict
from typing import List, Dict, Set, Optional, Tuple
from king_recreation.phonology_data import (
    Condition,
    VOWEL_SET,
    get_pronominal_set_name,
    use_glottal_grade,
    grades_are_compatible,
    StemType,
    MetathesisStrategy,
    PrePronominalConfig,
    PronominalConfig,
    get_prefix_details,
    detach_prefix,
)


@dataclass
class Derivation:
    pre_config: PrePronominalConfig
    pron_config: PronominalConfig
    consensus_stem: str
    stems: Dict[str, str]  # form_name -> stripped_stem (pronominal base)
    metathesis_involved: bool = False


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


def is_loose_compatible(s1: str, s2: str) -> bool:
    return bool(s1 and s2 and s1[0] == s2[0])


def strip_prepronominals(
    forms: Dict[str, str], config: PrePronominalConfig
) -> Optional[Dict[str, str]]:
    stripped = {}
    for fn, word in forms.items():
        current = word
        if config.translocutive:
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
            if fn in ["infinitive", "imperative"]:
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
    intermediate_forms: Dict[str, str], pron_config: PronominalConfig
) -> Optional[Derivation]:
    from king_recreation.phonology_data import get_prefix_details, detach_prefix

    derived_stems = {}
    metathesis_used = False
    for fn, word in intermediate_forms.items():
        set_name = get_pronominal_set_name(fn, pron_config)
        prefix, condition = get_prefix_details(set_name, pron_config)

        stem = detach_prefix(word, prefix, condition, pron_config.metathesis_strategy)
        if stem is None:
            return None

        # Check if metathesis was actually involved
        if condition in [Condition.METATHESIS_H_CONS, Condition.METATHESIS_VOWEL]:
            metathesis_used = True

        clean_pref = prefix.replace("-", "")
        if clean_pref == "ka" and word.startswith("kh"):
            metathesis_used = True

        derived_stems[fn] = stem
    h_grade = stems_are_consistent(derived_stems, pron_config)
    if h_grade:
        return Derivation(
            pre_config=None,
            pron_config=pron_config,
            consensus_stem=h_grade,
            stems=derived_stems,
            metathesis_involved=metathesis_used,
        )
    else:
        return None


def stems_are_consistent(
    derived_stems: dict[str, str], pron_config: PronominalConfig
) -> Optional[str]:
    """
    Check if a set of derived stems are consistent.

    1. Check that h grade stems are consisent
    2. Check that glottal grade stems are consistent
    3. Check that h and glottal grade stems match each other up to h alternation
    """
    h_candidate = derived_stems.get("present")
    g_candidate = derived_stems.get("present_1sg")

    # check that h and g grades are consistent within grades
    passing = True
    for fn, s in derived_stems.items():
        if use_glottal_grade(fn, pron_config):
            check = is_loose_compatible(s, g_candidate)
            passing &= check
        else:
            check = False
            # HOW DOES is strict compatible change this?
            if fn == "present":
                check = is_strict_compatible(s, h_candidate)
            else:
                check = is_loose_compatible(s, h_candidate)

            passing &= check

    if not passing:
        return None

    # check that grades are consistent together
    if g_candidate and not grades_are_compatible(h=h_candidate, glottal=g_candidate):
        return None

    return h_candidate


class StemDeriver:
    def derive_row(self, row: Dict[str, str]) -> List[Derivation]:
        form_names = [
            "present",
            "present_1sg",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]
        forms = {fn: row[fn] for fn in form_names if row.get(fn)}
        if not forms:
            return []
        valid_derivations = []
        for t in [False, True]:
            for p in [False, True]:
                for d in [False, True]:
                    pre_config = PrePronominalConfig(t, p, d)
                    intermediate = strip_prepronominals(forms, pre_config)
                    if intermediate is None:
                        continue
                    for set_type in ["a", "b"]:
                        for use_3rd in [False, True]:
                            for meta in MetathesisStrategy:
                                for s_type in StemType:
                                    ka_options = (
                                        [False, True] if set_type == "a" else [False]
                                    )
                                    uwa_options = [False, True]
                                    aki_options = [False, True]
                                    # uwa_options = [False, True] if set_type == 'b' else [False]
                                    # aki_options = [False, True] if set_type == 'b' else [False]
                                    for ka in ka_options:
                                        for uwa in uwa_options:
                                            for aki in aki_options:
                                                pron_config = PronominalConfig(
                                                    set_type=set_type,
                                                    stem_type=s_type,
                                                    metathesis_strategy=meta,
                                                    use_ka_variant=ka,
                                                    use_uwa_for_3rd_set_b=uwa,
                                                    use_aki_for_1st_set_b=aki,
                                                    use_3rd_person_object=use_3rd,
                                                )
                                                res = derive_pronominals(
                                                    intermediate, pron_config
                                                )
                                                if res:
                                                    res.pre_config = pre_config
                                                    valid_derivations.append(res)
        if not valid_derivations:
            return []
        valid_derivations.sort(
            key=lambda d: (
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
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_path = os.path.join(base_dir, "artifacts", "data", "corpus.csv")
    output_path = os.path.join(base_dir, "artifacts", "data", "stem_corpus.csv")
    failures_path = os.path.join(
        base_dir, "artifacts", "reports", "stem_derivation_failures.csv"
    )
    deriver = StemDeriver()
    labeled_data = []
    failures = []
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            derivations = deriver.derive_row(row)
            if not derivations:
                failures.append(row)
            else:
                d = derivations[0]
                for fn, stem in d.stems.items():
                    row[fn] = stem
                row["consensus_stem"] = d.consensus_stem
                row["set_a_b"] = d.pron_config.set_type
                row["translocutive"] = str(d.pre_config.translocutive)
                row["partitive"] = str(d.pre_config.partitive)
                row["distributive"] = str(d.pre_config.distributive)
                row["stem_type"] = d.pron_config.stem_type.value
                row["metathesis_strategy"] = d.pron_config.metathesis_strategy.value
                row["metathesis_involved"] = str(d.metathesis_involved)
                row["ka_variant"] = str(d.pron_config.use_ka_variant)
                row["uwa_3rd"] = str(d.pron_config.use_uwa_for_3rd_set_b)
                row["aki_1st"] = str(d.pron_config.use_aki_for_1st_set_b)
                row["3rd_person_object"] = str(d.pron_config.use_3rd_person_object)
                row["multiple_explanations"] = str(len(derivations) > 1)
                labeled_data.append(row)
    if labeled_data:
        keys = labeled_data[0].keys()
        with open(output_path, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(labeled_data)
    if failures:
        keys = failures[0].keys()
        with open(failures_path, "w", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(failures)
    print(f"Processed {len(labeled_data) + len(failures)} rows.")
    print(f"Success: {len(labeled_data)}")
    print(f"Failures: {len(failures)}")


if __name__ == "__main__":
    main()
