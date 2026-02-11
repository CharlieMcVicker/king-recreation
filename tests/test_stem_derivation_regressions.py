import csv
import os

import pytest

from king_recreation.derive_stems import (
    Derivation,
    StemDeriver,
    is_strict_compatible,
    strip_prepronominals,
)
from king_recreation.h_alternation import (
    _drop_first_h,
    _is_compatible_with_vowel_restoration,
)
from king_recreation.morphemes.prefixes.prepronominals import PrePronominalConfig
from king_recreation.morphemes.prefixes.pronominals import (
    MetathesisStrategy,
    PronominalConfig,
    StemType,
    detach_prefix,
    get_prefix_details,
    get_pronominal_set_name,
    use_glottal_grade,
)
from king_recreation.paths import corpus_no_asp_path
from king_recreation.phonology_data import VOWEL_SET


@pytest.fixture(scope="module")
def corpus_rows():
    if os.path.exists(corpus_no_asp_path):
        with open(corpus_no_asp_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
    else:
        print(f"Warning: Corpus file not found at {corpus_no_asp_path}")
        return []


@pytest.fixture
def deriver():
    return StemDeriver()


def diagnose_derivation(row, target_pron, target_pre):
    print(f"\n[DIAGNOSIS] Analyzing failure for definition: '{row.get('definition')}'")
    print(f"[DIAGNOSIS] Expected Config: {target_pron}")
    if target_pre:
        print(f"[DIAGNOSIS] Expected Pre-Config: {target_pre}")
    else:
        print(f"[DIAGNOSIS] No Pre-Config enforced (trying all valid pre-configs)")

    form_names = [
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    forms = {fn: row[fn] for fn in form_names if row.get(fn)}

    potential_pre_configs = []
    if target_pre:
        potential_pre_configs.append(target_pre)
    else:
        for t in [False, True]:
            for p in [False, True]:
                for d in [False, True]:
                    potential_pre_configs.append(PrePronominalConfig(t, p, d))

    successful_pre_strips = []
    for pc in potential_pre_configs:
        intermediate = strip_prepronominals(forms, pc, False)
        if intermediate:
            successful_pre_strips.append((pc, intermediate))

    if not successful_pre_strips:
        print(
            "[DIAGNOSIS] ALL Pre-Pronominal configurations failed to strip prefixes consistently."
        )
        return

    print(
        f"[DIAGNOSIS] Found {len(successful_pre_strips)} valid Pre-Pronominal strippings. Proceeding to check Pronominal logic."
    )

    any_pron_success = False

    for pc, intermediate in successful_pre_strips:
        print(f"\n[DIAGNOSIS] Testing PreConfig: {pc}")
        for use_3rd in [False, True]:
            print(f"  [DIAGNOSIS] Testing use_3rd_person_object='{use_3rd}'")

            derived_stems = {}
            failed_prefix = False

            # For diagnosis, we construct a temporary config to check prefixes
            check_config = PronominalConfig(
                set_type=target_pron.set_type,
                stem_type=target_pron.stem_type,
                metathesis_strategy=target_pron.metathesis_strategy,
                use_ka_variant=target_pron.use_ka_variant,
                long_start=target_pron.long_start,
                use_aki_for_1st_set_b=target_pron.use_aki_for_1st_set_b,
                use_3rd_person_object=use_3rd,
            )

            for fn, word in intermediate.items():
                stem, _ = detach_prefix(word, fn, check_config, False)

                if stem is None:
                    print(
                        f"    [FAILURE] Form '{fn}' ('{word}') failed to detach prefix for config"
                    )
                    failed_prefix = True
                else:
                    print(
                        f"    [SUCCESS] Form '{fn}' ('{word}') matches -> Stem: '{stem}'"
                    )
                    derived_stems[fn] = stem

            if failed_prefix:
                continue

            consensus_candidates = [
                s for fn, s in derived_stems.items() if fn != "present_1sg"
            ]
            if not consensus_candidates:
                consensus_candidates = list(derived_stems.values())
            consensus_stem = consensus_candidates[0]

            print(f"    [INFO] Candidate Consensus Stem: '{consensus_stem}'")

            consensus_fail = False
            for fn, s in derived_stems.items():
                if fn == "present_1sg":
                    continue
                is_h_drop = use_glottal_grade(fn, check_config, False)
                ref = _drop_first_h(consensus_stem) if is_h_drop else consensus_stem

                is_ok = False
                if fn == "present":
                    if is_strict_compatible(s, ref):
                        is_ok = True
                    elif is_h_drop and _is_compatible_with_vowel_restoration(s, ref):
                        is_ok = True
                else:
                    if is_strict_compatible(s, ref):
                        is_ok = True

                if not is_ok:
                    print(
                        f"    [FAILURE] Consensus Check Failed for '{fn}'. Derived: '{s}', Expected Ref: '{ref}'"
                    )
                    consensus_fail = True

            if consensus_fail:
                continue

            print("    [SUCCESS] Full Derivation Successful with this configuration!")
            any_pron_success = True

    if not any_pron_success:
        print(
            "\n[DIAGNOSIS] No successful derivation found with target pronominal config."
        )

    # Check if this config is reachable by derive_row
    s_type = target_pron.set_type
    allowed_ka = [False, True] if s_type == "a" else [False]
    allowed_uwa = [False, True]
    allowed_aki = [False, True]

    reachable = True
    if target_pron.use_ka_variant not in allowed_ka:
        reachable = False
    if target_pron.long_start not in allowed_uwa:
        reachable = False
    if target_pron.use_aki_for_1st_set_b not in allowed_aki:
        reachable = False

    if not reachable:
        print(
            f"\n[DIAGNOSIS CRITICAL WARNING] The expected configuration is NOT SEARCHED by derive_row due to set_type constraints."
        )
        print(f"  set_type='{s_type}' implies:")
        print(f"    allowed_ka = {allowed_ka} (Target: {target_pron.use_ka_variant})")
        print(f"    allowed_uwa = {allowed_uwa} (Target: {target_pron.long_start})")
        print(
            f"    allowed_aki = {allowed_aki} (Target: {target_pron.use_aki_for_1st_set_b})"
        )
        print(
            "  This explains why the test fails even if derivation logic succeeds above."
        )


TEST_CASES = [
    (
        "1. he's picking it up  2. he's getting it",
        PronominalConfig(set_type="a", stem_type=StemType.CONSONANT),
        None,
    ),
]


@pytest.mark.parametrize("definition, expected_pron, expected_pre", TEST_CASES)
def test_regressions(
    definition, expected_pron, expected_pre, corpus_rows, deriver, capsys
):
    if not corpus_rows:
        pytest.skip("No corpus rows loaded")

    # Find the row in the corpus
    matching_rows = [r for r in corpus_rows if r.get("definition") == definition]
    assert matching_rows, f"No row found in corpus for definition: {definition}"

    found_match = False
    for row in matching_rows:
        derivations = deriver.derive_row(row)
        for d in derivations:
            # 1. Full Derivation match
            if isinstance(expected_pron, Derivation):
                if d == expected_pron:
                    found_match = True
                    break
                else:
                    continue

            # 2. Config-based matching
            # Check PronominalConfig
            pron_match = True
            if isinstance(expected_pron, PronominalConfig):
                if d.config.pron != expected_pron:
                    pron_match = False
            elif isinstance(expected_pron, dict):
                for key, val in expected_pron.items():
                    if getattr(d.config.pron, key) != val:
                        pron_match = False
                        break

            # Check PrePronominalConfig if provided
            pre_match = True
            if expected_pre:
                if isinstance(expected_pre, PrePronominalConfig):
                    if d.config.pre != expected_pre:
                        pre_match = False
                elif isinstance(expected_pre, dict):
                    for key, val in expected_pre.items():
                        if getattr(d.config.pre, key) != val:
                            pre_match = False
                            break

            if pron_match and pre_match:
                found_match = True
                print(
                    f"    [MATCH FOUND] Consensus Stem: '{d.h_grade}', Metathesis Involved: {d.metathesis_involved}"
                )
                break
        if found_match:
            break

    if not found_match:
        # Extract configs if target is a full Derivation object
        diag_pron = expected_pron
        diag_pre = expected_pre
        if isinstance(expected_pron, Derivation):
            diag_pron = expected_pron.config.pron
            diag_pre = expected_pron.config.pre

        diagnose_derivation(matching_rows[0], diag_pron, diag_pre)

    assert (
        found_match
    ), f"No derivation for '{definition}' matched expected configurations."


def test_reject_stubbing_toe_bad_config(corpus_rows, deriver):
    """
    Regression test: "stubbing his toe" should NOT derive with the specific configuration
    that was previously found to be incorrect.
    """
    definition = "stubbing his toe"
    bad_pron_config = PronominalConfig(
        set_type="b",
        stem_type=StemType.ASPIRATED,
        metathesis_strategy=MetathesisStrategy.NONE,
        use_ka_variant=False,
        long_start=False,
        use_aki_for_1st_set_b=False,
        use_3rd_person_object=False,
    )
    bad_pre_config = PrePronominalConfig(
        translocutive=False, partitive=False, distributive=False
    )

    matching_rows = [r for r in corpus_rows if r.get("definition") == definition]
    assert matching_rows, f"No row found in corpus for definition: {definition}"
    row = matching_rows[0]

    derivations = deriver.derive_row(row)

    found_bad = False
    for d in derivations:
        if d.config.pron == bad_pron_config and d.config.pre == bad_pre_config:
            found_bad = True
            break

    assert (
        not found_bad
    ), "Should not derive 'stubbing his toe' with the rejected configuration."
