import csv
import sys

from king_recreation.derive_stems import Derivation, StemDeriver
from king_recreation.paths import corpus_path
from king_recreation.phonology_data import (
    PronominalConfig,
    StemType,
    get_pronominal_set_name,
)


def debug_derivation(target_definition):
    deriver = StemDeriver()
    row = None

    # Find the row in corpus.csv
    with open(corpus_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["definition"] == target_definition:
                row = r
                break

    if not row:
        print(
            f"Error: Could not find definition '{target_definition}' in artifacts/data/corpus.csv"
        )
        return

    print(f"Tracing derivation for: {row['definition']}")
    form_names = ["present", "imperfective", "perfective", "imperative", "infinitive"]
    forms = {fn: row[fn] for fn in form_names if row[fn]}
    print(f"Forms: {forms}")

    for set_type in ["Set A", "Set B"]:
        for use_3rd in [False, True]:
            for t in [True, False]:
                for p in [True, False]:
                    for d in [True, False]:
                        config = f"{set_type}, 3rd={use_3rd}, T={t}, P={p}, D={d}"

                        possible_stems = {fn: [] for fn in forms}

                        for fn, word in forms.items():
                            current_words = [("", word)]
                            for exists, p_type in [(t, "T"), (p, "P"), (d, "D")]:
                                next_words = []
                                for _, w in current_words:
                                    next_words.extend(
                                        deriver.match_prepronominal(
                                            w, exists, p_type, fn
                                        )
                                    )
                                current_words = list(set(next_words))

                            pron_config = PronominalConfig(
                                set_type=set_type,
                                stem_type=StemType.CONSONANT,
                                use_3rd_person_object=use_3rd,
                            )
                            pron_type = get_pronominal_set_name(fn, pron_config)
                            prefixes = deriver.prefixes_pronominal[pron_type]

                            for _, w in current_words:
                                for pref, cond in prefixes:
                                    if pref == "ø":
                                        if w and cond == "vowel_ae" and w[0] in "ae":
                                            possible_stems[fn].append(w)
                                    elif w.startswith(pref.replace("-", "")):
                                        remainder = w[len(pref.replace("-", "")) :]
                                        if cond == "a_replace":
                                            possible_stems[fn].append("a" + remainder)
                                        elif cond == "v" and pref == "uwa-":
                                            possible_stems[fn].append("v" + remainder)
                                        else:
                                            possible_stems[fn].append(remainder)

                        if all(stems for stems in possible_stems.values()):
                            # print(f"Valid per-form config: {config}")
                            # for fn, stems in possible_stems.items():
                            #    print(f"  {fn}: {stems}")

                            valid_present_stems = []
                            for ps in possible_stems["present"]:
                                if not ps:
                                    continue
                                initial = ps[0]
                                consistent = True
                                for fn in possible_stems:
                                    if not any(
                                        s and s[0] == initial
                                        for s in possible_stems[fn]
                                    ):
                                        consistent = False
                                        break
                                if consistent:
                                    valid_present_stems.append(ps)

                            if valid_present_stems:
                                print(f"SUCCESS: {config}")
                                print(f"  Stems: {valid_present_stems}")
                                return
                            else:
                                # Check WHY it's inconsistent
                                print(f"INCONSISTENT: {config}")
                                for fn, stems in possible_stems.items():
                                    print(f"  {fn}: {stems}")
                                # Check initial sounds
                                initials = {
                                    fn: set(s[0] for s in stems if s)
                                    for fn, stems in possible_stems.items()
                                }
                                print(f"  Initials: {initials}")

    print("\n--- Summary of failures for all configurations ---")
    # For a more detailed breakdown, let's re-run and print failures for likely configs
    # Most verbs are likely to have a specific P/T/D config.
    # Let's try to find if ANY config makes 'imperative' or 'perfective' work.

    for fn in forms:
        working_configs = 0
        for set_type in ["Set A", "Set B"]:
            for use_3rd in [False, True]:
                for t in [True, False]:
                    for p in [True, False]:
                        for d in [True, False]:
                            current_words = [("", forms[fn])]
                            for exists, p_type in [(t, "T"), (p, "P"), (d, "D")]:
                                next_words = []
                                for _, w in current_words:
                                    next_words.extend(
                                        deriver.match_prepronominal(
                                            w, exists, p_type, fn
                                        )
                                    )
                                current_words = list(set(next_words))

                            pron_config = PronominalConfig(
                                set_type=set_type,
                                stem_type=StemType.CONSONANT,
                                use_3rd_person_object=use_3rd,
                            )
                            pron_type = get_pronominal_set_name(fn, pron_config)
                            prefixes = deriver.prefixes_pronominal[pron_type]
                            can_derive = False
                            for _, w in current_words:
                                for pref, cond in prefixes:
                                    if pref == "ø":
                                        if w and cond == "vowel_ae" and w[0] in "ae":
                                            can_derive = True
                                    elif w.startswith(pref.replace("-", "")):
                                        can_derive = True
                            if can_derive:
                                working_configs += 1
        print(
            f"Form '{fn}' ({forms[fn]}) can be derived in {working_configs}/32 configurations."
        )


if __name__ == "__main__":
    target = "1. he's saying it  2. it's barking, meowing, whinnying, cooing, etc"
    debug_derivation(target)
