import csv
import os

from morphology.morphemes.prefixes import PrefixConfig
from morphology.morphemes.prefixes.prepronominals import PrePronominalConfig
from morphology.morphemes.prefixes.pronominals import PronominalConfig, StemType
from morphology.morphology_types import NounStructure, Number, Person, PronominalSet
from morphology.reconstruction import MorphologicalVerb, ReconstructionEngine, desegment
from morphology.word_spec import get_noun_wordspec


def clean_for_overlap(s: str) -> str:
    if not s:
        return ""
    return (
        s.replace(":", "")
        .replace("'", "")
        .replace("|", "")
        .replace("-", "")
        .strip()
        .lower()
    )


def phase_4_cross_reference(
    noun_stems_path: str | None = None,
    verb_roots_path: str | None = None,
    output_path: str | None = None,
):
    if noun_stems_path is None:
        noun_stems_path = os.path.join(
            "artifacts", "corpora", "validated_noun_stems.csv"
        )
    if verb_roots_path is None:
        verb_roots_path = os.path.join("artifacts", "data", "roots_by_class.csv")
    if output_path is None:
        output_path = os.path.join(
            "artifacts", "corpora", "noun_verb_cross_reference.csv"
        )

    if not os.path.exists(noun_stems_path):
        print(f"Noun stems file not found at {noun_stems_path}")
        return

    if not os.path.exists(verb_roots_path):
        print(f"Verb roots file not found at {verb_roots_path}")
        return

    # Load verb roots
    verb_roots = []
    with open(verb_roots_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            verb_roots.append(
                {
                    "root_id": row["root_id"].strip(),
                    "h_grade": row["h_grade"].strip(),
                    "g_grade": row["g_grade"].strip(),
                    "class": row["class"].strip(),
                    "stem_type": row["stem_type"].strip(),
                    "corpus_ids": row["corpus_ids"].strip(),
                }
            )

    # Initialize Reconstruction Engine
    engine = ReconstructionEngine(None)

    # Load and process validated noun stems
    matches = []
    seen_matches = set()
    with open(noun_stems_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("is_valid") != "True":
                continue

            corpus_id = row["corpus_id"]
            original_word = row["original_word"]
            noun_template = row["noun_template"]
            noun_verb_root = row["verb_root"]

            # Reconstruct WordSpec
            structure_str = row.get("structure")
            person_str = row.get("person")
            number_str = row.get("number")
            pronominal_set_str = row.get("pronominal_set")

            structure = (
                NounStructure(noun_template) if noun_template else NounStructure.ROOT
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

            # Match against each verb root
            clean_noun_root = clean_for_overlap(noun_verb_root)
            clean_noun_word = clean_for_overlap(original_word)

            for verb in verb_roots:
                h_grade = verb["h_grade"]
                g_grade = verb["g_grade"]

                # 1. Direct Match (check if noun verb_root matches h_grade or g_grade)
                # Note: Do NOT match against root_id as requested
                is_direct = False
                if noun_verb_root:
                    if (h_grade and noun_verb_root == h_grade) or (
                        g_grade and noun_verb_root == g_grade
                    ):
                        is_direct = True

                if is_direct:
                    match_key = (
                        corpus_id,
                        original_word,
                        noun_template,
                        verb["root_id"],
                        verb["class"],
                        verb["corpus_ids"],
                        "direct",
                    )
                    if match_key not in seen_matches:
                        seen_matches.add(match_key)
                        matches.append(
                            {
                                "noun_corpus_id": corpus_id,
                                "noun_original_word": original_word,
                                "noun_template": noun_template,
                                "matched_verb_root_id": verb["root_id"],
                                "matched_verb_class": verb["class"],
                                "matched_verb_corpus_ids": verb["corpus_ids"],
                                "match_type": "direct",
                            }
                        )
                    continue

                # 2. Reconstruction fallback
                # Run prefix/overlap check to optimize speed
                clean_h = clean_for_overlap(h_grade)
                clean_g = clean_for_overlap(g_grade)

                overlap = (
                    (clean_h and clean_h in clean_noun_word)
                    or (clean_g and clean_g in clean_noun_word)
                    or (clean_noun_root and clean_h and clean_noun_root in clean_h)
                    or (clean_noun_root and clean_g and clean_noun_root in clean_g)
                )
                if not overlap:
                    continue

                # Construct MorphologicalVerb
                try:
                    v_stem_type = StemType(verb["stem_type"])
                except ValueError:
                    # Fallback to consonant if not recognized
                    v_stem_type = StemType.CONSONANT

                morph_verb = MorphologicalVerb(
                    h_grade_root=h_grade,
                    glottal_grade_root=g_grade if g_grade else h_grade,
                    post_root_morpheme=None,
                    class_name=verb["class"],
                    config=PrefixConfig(
                        pre=PrePronominalConfig(),
                        pron=PronominalConfig(
                            set_type=pronominal_set or PronominalSet.SET_A,
                            stem_type=v_stem_type,
                        ),
                    ),
                )

                reconstructed_forms = engine.reconstruct_spec(morph_verb, word_spec)
                desegmented_forms = [desegment(f) for f in reconstructed_forms]

                if original_word in desegmented_forms:
                    match_key = (
                        corpus_id,
                        original_word,
                        noun_template,
                        verb["root_id"],
                        verb["class"],
                        verb["corpus_ids"],
                        "reconstruction",
                    )
                    if match_key not in seen_matches:
                        seen_matches.add(match_key)
                        matches.append(
                            {
                                "noun_corpus_id": corpus_id,
                                "noun_original_word": original_word,
                                "noun_template": noun_template,
                                "matched_verb_root_id": verb["root_id"],
                                "matched_verb_class": verb["class"],
                                "matched_verb_corpus_ids": verb["corpus_ids"],
                                "match_type": "reconstruction",
                            }
                        )

    # Write output to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fieldnames = [
        "noun_corpus_id",
        "noun_original_word",
        "noun_template",
        "matched_verb_root_id",
        "matched_verb_class",
        "matched_verb_corpus_ids",
        "match_type",
    ]
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for m in matches:
            writer.writerow(m)

    print(f"Cross-referenced {len(matches)} matches and saved to {output_path}")


if __name__ == "__main__":
    phase_4_cross_reference()
