from dictionary_pipeline.utils import clean_string, respell_consonants, read_original_cnd
import os
import re
from typing import Any

from dictionary_pipeline.dictionary_forms import ROW_PREDICTION_SPECS
from dictionary_pipeline.phases.preprocess_ced.artifacts import (
    load_manual_corrections,
    save_corpus,
    save_mapping,
    save_raw_corpus,
)
from dictionary_pipeline.row_models import (
    CorpusForms,
    PatchRow,
    Prediction,
    PredictionMeta,
    ProcessedRow,
)


def apply_patches(
    data: list[ProcessedRow], corrections: list[PatchRow]
) -> list[ProcessedRow]:
    """
    Apply patches to the corpus data.
    """
    from collections import defaultdict

    # Create a mapping for quick lookup of all rows with a given corpus_id
    data_map = defaultdict(list)
    for row in data:
        data_map[str(row.meta.corpus_id)].append(row)

    for patch in corrections:
        corpus_id = str(patch.meta.corpus_id).strip()
        if not corpus_id:
            continue

        if corpus_id in data_map:
            for target_row in data_map[corpus_id]:
                for field_name in ["entry_no", "definition"]:
                    value = getattr(patch.meta, field_name)
                    if value == "NULL":
                        value = ""
                    elif isinstance(value, str) and not (value and value.strip()):
                        continue
                    if isinstance(value, str):
                        value = value.strip()
                    setattr(target_row.meta, field_name, value)

                for field_name in [
                    "present",
                    "present_1sg",
                    "imperfective",
                    "perfective",
                    "imperative",
                    "infinitive",
                ]:
                    value = getattr(patch.forms, field_name)
                    if value == "NULL":
                        value = ""
                    elif not (value and value.strip()):
                        continue

                    value = value.strip()
                    setattr(target_row.forms, field_name, value)

    return data


def clean_row(row: dict[str, str]) -> dict[str, Any]:
    definition = row.get("definition", "").strip()

    present = clean_string(row.get("3rd present", ""))
    present_1sg = clean_string(row.get("1st present", ""))

    imperfective_raw = row.get("3rd incompletive habitual", "")
    imperfective = clean_string(imperfective_raw)

    perfective_raw = row.get("3rd completive past", "")
    perfective = clean_string(perfective_raw)

    imperative = clean_string(row.get("2nd imperative", ""))

    infinitive_raw = row.get("3rd infinitive", "")
    infinitive = clean_string(infinitive_raw)

    return {
        "definition": definition,
        "present": present,
        "present_1sg": present_1sg,
        "imperfective": imperfective,
        "perfective": perfective,
        "imperative": imperative,
        "infinitive": infinitive,
    }


def create_corpus_from_cn_dict() -> None:
    """
    Create a corpus CSV with one row per lexical item.

    Inputs:
    * CHEROKEE_NATION_DICTIONARY_PATH: a CSV with one row per verb form, multiple orthographies.

    Outputs:
    * CORPUS_PATH: a CSV with one row per lexical item with all forms present, tone-less orthography.
    """
    rows = read_original_cnd()

    # Load manual corrections to check for prediction overrides
    import csv as std_csv

    from dictionary_pipeline.paths import MANUAL_CORRECTIONS_PATH

    corrections_raw = []
    if os.path.exists(MANUAL_CORRECTIONS_PATH):
        with open(MANUAL_CORRECTIONS_PATH, mode="r", encoding="utf-8") as f:
            corrections_raw = list(std_csv.DictReader(f))

    corrections_map = {}
    for r in corrections_raw:
        cid = r.get("corpus_id", "").strip()
        if cid:
            corrections_map[cid] = r

    # Group rows by "Entry No." (Using "No." column as primary ID, but it seems to repeat for forms)
    # The file has "No." column which groups forms of the same verb.
    # We will read all rows and group them by "No."

    grouped_entries = {}
    for row in rows:
        entry_no = row.get("No.", "").strip()
        if not entry_no:
            continue

        if entry_no not in grouped_entries:
            grouped_entries[entry_no] = []
        grouped_entries[entry_no].append(row)

    processed_data = []
    mapping_data = []

    for idx, (entry_no, rows) in enumerate(grouped_entries.items()):
        # Build a single verb dictionary from the rows
        verb_data = {
            "corpus_id": str(idx),
            "entry_no": entry_no,
            "definition": "",
            "present": "",
            "present_1sg": "",
            "imperfective": "",
            "perfective": "",
            "imperative": "",
            "infinitive": "",
        }

        mapping_entry = {
            "corpus_id": str(idx),
            "present": "",
            "present_1sg": "",
            "imperfective": "",
            "perfective": "",
            "imperative": "",
            "infinitive": "",
        }

        # Determine if this group is a verb.
        is_verb = False
        parts_of_speech = set()
        for row in rows:
            pos = row.get("Part of speech", "").lower()
            parts_of_speech.add(pos)
            if pos.startswith("verb"):
                is_verb = True

        if not is_verb:
            continue

        # Get definition from the first row that has one
        for row in rows:
            gloss = row.get("Translation 1A", "").strip()
            extra = row.get("Translation 1 sub entry")

            if extra:
                gloss = f"{gloss} ({extra})"

            if gloss:
                verb_data["definition"] = gloss
                break

        # Determine forms using best-match logic (matching frontend getCorpusForm)
        def get_priority(sub):
            if "animate" in sub and "inanimate" not in sub:
                return 3
            if "animate" in sub:
                return 2
            if "inanimate" in sub:
                return 1
            return 0

        def select_form(predicate):
            best_form = ""
            best_entry_no = ""
            best_priority = -1
            for row in rows:
                sub = row.get("Grammar sub entry", "").strip().lower()
                if predicate(sub):
                    p = get_priority(sub)
                    if p > best_priority:
                        best_form = row.get("Practical", "").strip()
                        best_entry_no = row.get("Entry No.", "").strip()
                        best_priority = p
            return clean_string(best_form), best_entry_no

        # Present
        form, cnd_no = select_form(
            lambda s: s.startswith("3rd person singular")
            and not any(x in s for x in ["habitual", "past", "infinitive"])
        )
        verb_data["present"] = form
        mapping_entry["present"] = cnd_no

        # Present 1sg
        form, cnd_no = select_form(lambda s: s.startswith("1st person singular"))
        verb_data["present_1sg"] = form
        mapping_entry["present_1sg"] = cnd_no

        # Perfective
        form, cnd_no = select_form(lambda s: "remote past" in s)
        verb_data["perfective"] = form
        mapping_entry["perfective"] = cnd_no

        # Imperfective
        form, cnd_no = select_form(lambda s: "habitual" in s)
        verb_data["imperfective"] = form
        mapping_entry["imperfective"] = cnd_no

        # Imperative
        form, cnd_no = select_form(lambda s: "imperative" in s)
        verb_data["imperative"] = form
        mapping_entry["imperative"] = cnd_no

        # Infinitive
        form, cnd_no = select_form(lambda s: "infinitive" in s)
        verb_data["infinitive"] = form
        mapping_entry["infinitive"] = cnd_no

        if (
            sum(
                1
                for form in [
                    "present",
                    "present_1sg",
                    "imperfective",
                    "perfective",
                    "imperative",
                    "infinitive",
                ]
                if verb_data.get(form)
            )
            > 1
        ):
            # Check if there is an override for this corpus_id
            corpus_id_str = str(verb_data["corpus_id"])
            forced_spec_name = None
            patch = corrections_map.get(corpus_id_str)
            if patch:
                forced_spec_name = patch.get("prediction", "").strip() or None

            specs_to_try = ROW_PREDICTION_SPECS
            if forced_spec_name:
                specs_to_try = [
                    s for s in ROW_PREDICTION_SPECS if s.name == forced_spec_name
                ]

            for spec in specs_to_try:
                # If prediction is forced, bypass row_test check
                if not forced_spec_name and not spec.row_test(verb_data):
                    continue
                for prediction, test in spec.predictions:
                    if not test(verb_data):
                        continue
                    row = ProcessedRow(
                        meta=PredictionMeta(
                            corpus_id=str(verb_data["corpus_id"]),
                            definition=verb_data["definition"],
                            entry_no=verb_data["entry_no"],
                            prediction=Prediction(prediction),
                        ),
                        forms=CorpusForms(
                            present=verb_data.get("present", ""),
                            present_1sg=verb_data.get("present_1sg", ""),
                            imperfective=verb_data.get("imperfective", ""),
                            perfective=verb_data.get("perfective", ""),
                            imperative=verb_data.get("imperative", ""),
                            infinitive=verb_data.get("infinitive", ""),
                        ),
                    )
                    processed_data.append(row)
                    mapping_data.append(mapping_entry)

    save_raw_corpus(processed_data)

    corrections = load_manual_corrections()
    if corrections:
        processed_data = apply_patches(processed_data, corrections)

    save_corpus(processed_data)

    mapping_fieldnames = [
        "corpus_id",
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    save_mapping(mapping_data, mapping_fieldnames)


if __name__ == "__main__":
    create_corpus_from_cn_dict()
