import csv
import os
import dataclasses
from dataclasses import dataclass
from typing import List

from morphology.reconstruction import ReconstructionEngine, MorphologicalVerb, desegment
from morphology.morphemes.prefixes import PrefixConfig
from morphology.morphemes.aspect.pattern_registry import PatternRegistry
from morphology.morphology_types import Number, Person, PronominalSet
from morphology.word_spec import NounStructure, WordSpec, get_noun_wordspec
from noun_pipeline.phases.generate_hypotheses import NounHypothesis


@dataclass
class ValidatedNounStem:
    original_word: str
    word_spec: WordSpec
    stem: str
    noun_template: str
    verb_root: str
    paradigm: str
    plural_paradigm: str
    is_valid: bool


def extract_and_validate_stems(
    hypotheses: List[NounHypothesis],
) -> List[ValidatedNounStem]:
    registry = PatternRegistry.get_instance()
    registry.load_from_csv()
    
    engine = ReconstructionEngine(None)

    validated = []

    for h in hypotheses:
        aspect = h.word_spec.aspect
        noun_template = h.noun_template

        if aspect is None:
            validated.append(
                ValidatedNounStem(
                    original_word=h.original_word,
                    word_spec=h.word_spec,
                    stem=h.stem,
                    noun_template=noun_template,
                    verb_root=h.stem,
                    paradigm="root",
                    plural_paradigm="unknown",
                    is_valid=True,
                )
            )
            continue

        candidates = registry.get_candidates(
            h.stem, aspect.value, allow_suffix_alternation=True
        )

        is_valid = False
        verb_root = ""
        paradigm = ""
        plural_paradigm = "unknown"

        for cand in candidates:
            root = cand.strip_form(aspect, h.stem)
            if root is not None:
                is_valid = True
                verb_root = root
                paradigm = cand.name
                
                if h.plural_word:
                    from morphology.morphemes.prefixes.pronominals import StemType, PronominalConfig
                    from morphology.morphemes.prefixes.prepronominals import PrePronominalConfig
                    
                    verb = MorphologicalVerb(
                        h_grade_root=verb_root,
                        glottal_grade_root=verb_root,
                        post_root_morpheme=None,
                        class_name=paradigm,
                        config=PrefixConfig(
                            pre=PrePronominalConfig(),
                            pron=PronominalConfig(
                                set_type=h.word_spec.pronominal_set or PronominalSet.SET_A,
                                stem_type=StemType.CONSONANT
                            )
                        ),
                    )
                    plural_spec = dataclasses.replace(h.word_spec, number=Number.PLURAL)
                    animate_forms = engine.reconstruct_spec(verb, plural_spec)
                    animate_desegmented = [desegment(f) for f in animate_forms]
                    
                    inanimate_verb = MorphologicalVerb(
                        h_grade_root=verb_root,
                        glottal_grade_root=verb_root,
                        post_root_morpheme=None,
                        class_name=paradigm,
                        config=PrefixConfig(
                            pre=PrePronominalConfig(distributive=True),
                            pron=PronominalConfig(
                                set_type=h.word_spec.pronominal_set or PronominalSet.SET_A,
                                stem_type=StemType.CONSONANT
                            )
                        ),
                    )
                    inanimate_forms = engine.reconstruct_spec(inanimate_verb, h.word_spec)
                    inanimate_desegmented = [desegment(f) for f in inanimate_forms]
                    
                    if h.plural_word in animate_desegmented:
                        plural_paradigm = "animate"
                    elif h.plural_word in inanimate_desegmented:
                        plural_paradigm = "inanimate"
                    else:
                        is_valid = False
                        plural_paradigm = "unknown"
                
                if is_valid:
                    break

        validated.append(
            ValidatedNounStem(
                original_word=h.original_word,
                word_spec=h.word_spec,
                stem=h.stem,
                noun_template=noun_template,
                verb_root=verb_root,
                paradigm=paradigm,
                plural_paradigm=plural_paradigm,
                is_valid=is_valid,
            )
        )

    return validated


def phase_3_extract_stems():
    input_path = os.path.join("artifacts", "corpora", "noun_hypotheses.csv")
    output_path = os.path.join("artifacts", "corpora", "validated_noun_stems.csv")

    if not os.path.exists(input_path):
        print(f"Hypotheses not found at {input_path}")
        return

    hypotheses = []
    corpus_ids = []
    
    with open(input_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            structure_str = row.get("structure")
            person_str = row.get("person")
            number_str = row.get("number")
            pronominal_set_str = row.get("pronominal_set")

            structure = (
                NounStructure(structure_str) if structure_str else NounStructure.ROOT
            )

            person = Person(person_str) if person_str else None
            number = Number(number_str) if number_str else None
            pronominal_set = (
                PronominalSet(pronominal_set_str) if pronominal_set_str else None
            )

            word_spec = get_noun_wordspec(
                structure=structure,
                person=person,
                number=number,
                pronominal_set=pronominal_set,
            )

            h = NounHypothesis(
                original_word=row["original_word"],
                word_spec=word_spec,
                stem=row["stem"],
                noun_template=structure.value,
                plural_word=row.get("plural_word") or None,
            )
            hypotheses.append(h)
            corpus_ids.append(row.get("corpus_id", ""))

    validated_stems = extract_and_validate_stems(hypotheses)

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
        "noun_template",
        "verb_root",
        "paradigm",
        "plural_paradigm",
        "is_valid",
    ]

    valid_count = 0
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for i, val in enumerate(validated_stems):
            writer.writerow(
                {
                    "corpus_id": corpus_ids[i],
                    "original_word": val.original_word,
                    "stem": val.stem,
                    "structure": (
                        val.word_spec.syntactic_category.value
                        if val.word_spec.syntactic_category
                        else ""
                    ),
                    "aspect": (
                        val.word_spec.aspect.value if val.word_spec.aspect else ""
                    ),
                    "person": (
                        val.word_spec.person.value if val.word_spec.person else ""
                    ),
                    "number": (
                        val.word_spec.number.value if val.word_spec.number else ""
                    ),
                    "pronominal_set": (
                        val.word_spec.pronominal_set.value
                        if val.word_spec.pronominal_set
                        else ""
                    ),
                    "noun_template": val.noun_template,
                    "verb_root": val.verb_root,
                    "paradigm": val.paradigm,
                    "plural_paradigm": val.plural_paradigm,
                    "is_valid": str(val.is_valid),
                }
            )
            if val.is_valid:
                valid_count += 1

    print(
        f"Validated {valid_count}/{len(validated_stems)} stems and saved to {output_path}"
    )

if __name__ == "__main__":
    phase_3_extract_stems()
