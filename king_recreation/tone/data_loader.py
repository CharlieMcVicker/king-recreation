import io
import json
from csv import DictReader, DictWriter
from typing import List, Union

from king_recreation.paths import (
    CHEROKEE_NATION_DICTIONARY_PATH,
    CORPUS_TO_CND_PATH,
    RECONSTRUCTABLE_VERBS_PATH,
    STEMS_WITH_TONE_CORPUS_PATH,
)
from king_recreation.reconstruct_from_roots import ReconstructibleVerb
from king_recreation.tone.utils import (
    Consonant,
    Vowel,
    apply_tone_to_segmentation,
    get_tone_sequence_for_form,
)


def load_data():
    """Load the necessary data for tone analysis."""
    with open(RECONSTRUCTABLE_VERBS_PATH, "r") as f:
        reconstructable_verbs_raw = json.load(f)
    verbs = [ReconstructibleVerb.from_dict(v) for v in reconstructable_verbs_raw]

    with open(CORPUS_TO_CND_PATH, "r") as f:
        reader = DictReader(f)
        corpus_id_to_entries = {int(r["corpus_id"]): r for r in reader}

    with open(CHEROKEE_NATION_DICTIONARY_PATH, "r") as f:
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
    - No animate object-pronouns
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

    if verb.config.pron.use_3rd_person_object:
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
        with open(STEMS_WITH_TONE_CORPUS_PATH, "w", newline="") as f:
            # Use the second element of the tuple which is the dictionary
            writer = DictWriter(f, fieldnames=rows[0][1].keys())
            writer.writeheader()
            writer.writerows([row[1] for row in rows])

        print(
            f"\nScaffold complete. Processed {len(verbs)} verbs, {eligible_count} were eligible for analysis."
        )

    return rows
