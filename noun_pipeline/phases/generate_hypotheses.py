import csv
import os
from dataclasses import dataclass
from typing import List

from morphology.morphemes.prefixes.pronominals import (
    PronominalConfig,
    StemType,
    detach_prefix,
)
from morphology.morphology_types import Number, Person, PronominalSet
from morphology.word_spec import NounStructure, WordSpec, get_noun_wordspec


@dataclass
class NounHypothesis:
    original_word: str
    word_spec: WordSpec
    stem: str


def generate_hypotheses(noun: str) -> List[NounHypothesis]:
    hypotheses = []

    # Define possible suffixes and their structural mappings
    suffix_rules = [
        ("i", NounStructure.AGENTIVE),
        ("v'i", NounStructure.COMPLETIVE),
        ("v'i", NounStructure.INCOMPLETIVE),
        ("", NounStructure.ROOT),
    ]

    # 3rd person prefix keys to try detaching
    pronominal_keys = [
        (Person.THIRD, Number.SINGULAR, PronominalSet.SET_A),
        (Person.THIRD, Number.PLURAL, PronominalSet.SET_A),
        (Person.THIRD, Number.SINGULAR, PronominalSet.SET_B),
        (Person.THIRD, Number.PLURAL, PronominalSet.SET_B),
    ]

    for suffix, structure in suffix_rules:
        if suffix == "" or noun.endswith(suffix):
            base_word = noun[: -len(suffix)] if suffix else noun

            # Hypothesis 1: No pronominal stripped
            word_spec_no_pron = get_noun_wordspec(structure)
            h_no_pron = NounHypothesis(noun, word_spec_no_pron, base_word)
            if h_no_pron not in hypotheses:
                hypotheses.append(h_no_pron)

            # Try to strip pronominals
            for person, number, p_set in pronominal_keys:
                key = (person, number, p_set)

                for stem_type in StemType:
                    for use_ka_variant in [False, True]:
                        config = PronominalConfig(
                            set_type=p_set,
                            stem_type=stem_type,
                            use_ka_variant=use_ka_variant,
                        )

                        try:
                            stem, metathesis = detach_prefix(base_word, key, config)
                            if stem is not None and stem_type.is_valid_for_stem(stem):
                                word_spec = get_noun_wordspec(
                                    structure,
                                    person=person,
                                    number=number,
                                    pronominal_set=p_set,
                                )
                                hypothesis = NounHypothesis(noun, word_spec, stem)
                                if hypothesis not in hypotheses:
                                    hypotheses.append(hypothesis)
                        except Exception:
                            continue

    return hypotheses


def phase_2_generate_hypotheses():
    corpus_path = os.path.join("artifacts", "corpora", "nouns_corpus.csv")
    output_path = os.path.join("artifacts", "corpora", "noun_hypotheses.csv")

    if not os.path.exists(corpus_path):
        print(f"Corpus not found at {corpus_path}")
        return

    all_hypotheses = []

    with open(corpus_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            word = row.get("singular", "")
            if word:
                hyps = generate_hypotheses(word)
                for h in hyps:
                    all_hypotheses.append(
                        {
                            "corpus_id": row["corpus_id"],
                            "original_word": h.original_word,
                            "stem": h.stem,
                            "structure": h.word_spec.syntactic_category.value,
                            "aspect": (
                                h.word_spec.aspect.value if h.word_spec.aspect else ""
                            ),
                            "person": (
                                h.word_spec.person.value if h.word_spec.person else ""
                            ),
                            "number": (
                                h.word_spec.number.value if h.word_spec.number else ""
                            ),
                            "pronominal_set": (
                                h.word_spec.pronominal_set.value
                                if h.word_spec.pronominal_set
                                else ""
                            ),
                        }
                    )

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = [
        "corpus_id",
        "original_word",
        "stem",
        "structure",
        "aspect",
        "person",
        "number",
        "pronominal_set",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_hypotheses)

    print(f"Generated {len(all_hypotheses)} hypotheses and saved to {output_path}")
