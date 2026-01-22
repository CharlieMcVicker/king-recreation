import csv
import re
import os


def respell_consonants(s):
    # Rewrite rules for aspiration marking
    # Order matters: t->th before d->t, k->kh before g->k
    # Exception: ts should stay ts (not become ths)

    # We want to replace 't' with 'th' only if it's not followed by 's'
    s = re.sub(r"t(?!s)", "th", s)

    rules = [
        # ("t", "th"), # Handled by regex above to allow for ts exception
        ("d", "t"),
        ("k", "kh"),
        ("g", "k"),
        ("j", "ts"),
        ("ch", "tsh"),
        ("hn", "nh"),
        ("hl", "lh"),
        ("hy", "yh"),
        ("hw", "wh"),
        ("?", "'"),
        ("’", "'"),
    ]
    for old, new in rules:
        s = s.replace(old, new)

    s = re.sub(r"sl(?=[aeiouv])", "slh", s)
    s = re.sub(r"([^ht])s", r"\1hs", s)

    return s


def clean_string(s):
    if not s or s == "-----":
        return ""
    # Remove tones [1234], glottal stops [?], periods [.], and apostrophes ['’] (which are glottal stops in new source)
    # README says tone markings /[1234\.]/ and glottal stops /\?/
    s = re.sub(r"[1234\.]", "", s)
    return respell_consonants(s)


def clean_row(row):
    definition = row.get("definition", "").strip()

    present = clean_string(row.get("3rd present", ""))
    # README: "3rd present column with final i or a rstripped; for ia only a is dropped"
    if present.endswith("i'a"):
        present = present[:-1]
    elif present.endswith("i") or present.endswith("a"):
        present = present[:-1]

    present_1sg = clean_string(row.get("1st present", ""))
    # Same logic as 3rd present: strip final i or a
    if present_1sg.endswith("i'a"):
        present_1sg = present_1sg[:-1]
    elif present_1sg.endswith("i") or present_1sg.endswith("a"):
        present_1sg = present_1sg[:-1]

    imperfective_raw = row.get("3rd incompletive habitual", "")
    imperfective = clean_string(imperfective_raw)
    # README: "3rd incompletive habitual column with oi rstripped"
    # Logic: if it ends in 'i' (possibly with tones/glottals), and has 'o' before it.
    print(imperative[:-3], imperfective.endswith("o'i"))
    if imperfective.endswith("o'i"):
        imperfective = imperfective[:-3]

    perfective_raw = row.get("3rd completive past", "")
    perfective = clean_string(perfective_raw)
    # README: "3rd completive past column with vi rstripped"
    if perfective.endswith("v'i"):
        perfective = perfective[:-3]

    imperative = clean_string(row.get("2nd imperative", ""))

    infinitive_raw = row.get("3rd infinitive", "")
    infinitive = clean_string(infinitive_raw)
    # README: "3rd infinitive column with i rstripped"
    if infinitive.endswith("i"):
        infinitive = infinitive[:-1]

    return {
        "definition": definition,
        "present": present,
        "present_1sg": present_1sg,
        "imperfective": imperfective,
        "perfective": perfective,
        "imperative": imperative,
        "infinitive": infinitive,
    }


def process_cn_dict(file_path, output_path):
    print(f"Processing Cherokee Nation dictionary from {file_path}")

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: Input file needed not found at {file_path}")
        return

    # Ensure the full directory path exists for the output file
    output_data_dir = os.path.dirname(output_path)
    if not os.path.exists(output_data_dir):
        os.makedirs(output_data_dir)

    # Group rows by "Entry No." (Using "No." column as primary ID, but it seems to repeat for forms)
    # The file has "No." column which groups forms of the same verb.
    # We will read all rows and group them by "No."

    grouped_entries = {}

    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry_no = row.get("No.", "").strip()
            if not entry_no:
                continue

            if entry_no not in grouped_entries:
                grouped_entries[entry_no] = []
            grouped_entries[entry_no].append(row)

    processed_data = []

    for idx, (entry_no, rows) in enumerate(grouped_entries.items()):
        # Build a single verb dictionary from the rows
        verb_data = {
            "entry_no": entry_no,
            "definition": "",
            "present": "",
            "present_1sg": "",
            "imperfective": "",
            "perfective": "",
            "imperative": "",
            "infinitive": "",
        }

        # We need to find the definition. Usually in the first row or headword row.
        # But we can just take the first definition found or specific one.
        # Using "English gloss 1" seems appropriate from the requested file view.
        # Or "Translation 1A". Let's stick to accumulating forms first.

        # Determine if this group is a verb.
        # Check "Part of speech" column for any row.
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
            best_priority = -1
            for row in rows:
                sub = row.get("Grammar sub entry", "").strip().lower()
                if predicate(sub):
                    p = get_priority(sub)
                    if p > best_priority:
                        best_form = row.get("Practical", "").strip()
                        best_priority = p
            return clean_string(best_form)

        verb_data["present"] = select_form(
            lambda s: s.startswith("3rd person singular")
            and not any(x in s for x in ["habitual", "past", "infinitive"])
        )
        verb_data["present_1sg"] = select_form(
            lambda s: s.startswith("1st person singular")
        )
        verb_data["perfective"] = select_form(lambda s: "remote past" in s)
        verb_data["imperfective"] = select_form(lambda s: "habitual" in s)
        verb_data["imperative"] = select_form(lambda s: "imperative" in s)
        verb_data["infinitive"] = select_form(lambda s: "infinitive" in s)

        # Apply the final suffix stripping logic (clean_row logic) to the extracted values
        # Since clean_row expects raw values with suffixes, and clean_string does initial cleaning,
        # we might need to adjust. clean_row logic:
        # present: rstrip i or a (or ia)
        # imperfective: rstrip oi
        # perfective: rstrip vi
        # infinitive: rstrip i
        # NOTE: clean_string is already applied. We just need to apply the suffix stripping now.

        # Present
        p = verb_data["present"]
        if p.endswith("i") or p.endswith("a"):
            verb_data["present"] = p[:-1]

        # Present 1sg
        p1 = verb_data["present_1sg"]
        if p1.endswith("i") or p1.endswith("a"):
            verb_data["present_1sg"] = p1[:-1]

        # Imperfective
        imp = verb_data["imperfective"]
        if imp.endswith("o'i"):
            verb_data["imperfective"] = imp[:-3]

        # Perfective
        perf = verb_data["perfective"]
        if perf.endswith("v'i"):
            verb_data["perfective"] = perf[:-3]

        # Infinitive
        inf = verb_data["infinitive"]
        if inf.endswith("i"):
            verb_data["infinitive"] = inf[:-1]

        # Only add if we have at least a present form or something substantial?
        # The existing logic doesn't explicitly filter but empty strings result in empty columns.
        verb_data["corpus_id"] = idx
        processed_data.append(verb_data)

    fieldnames = [
        "corpus_id",
        "entry_no",
        "definition",
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]

    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_data)

    print(f"Processed CN data written to {output_path}")


def process_ced():
    input_path = "data/ced_data_original.csv"
    output_dir = "artifacts"
    # The instruction implies a base_dir, but it's not defined.
    # Assuming the intent is to place it within 'artifacts/data/' relative to the script.
    output_path = os.path.join(output_dir, "data", "corpus.csv")

    # Ensure the full directory path exists for the output file
    output_data_dir = os.path.dirname(output_path)
    if not os.path.exists(output_data_dir):
        os.makedirs(output_data_dir)

    processed_data = []

    with open(input_path, mode="r", encoding="utf-8") as f:
        # The file seems to have a trailing comma in the header based on initial view
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            verb_data = clean_row(row)
            verb_data["corpus_id"] = idx
            processed_data.append(verb_data)

    fieldnames = [
        "corpus_id",
        "definition",
        "present",
        "present_1sg",
        "imperfective",
        "perfective",
        "imperative",
        "infinitive",
    ]
    with open(output_path, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_data)

    print(f"Processed data written to {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--new-source",
        action="store_true",
        help="Use the new Cherokee Nation dictionary source",
    )
    args = parser.parse_args()

    if args.new_source:
        process_cn_dict(
            "data/cherokee_nation_dictionary.csv", "artifacts/data/corpus.csv"
        )
    else:
        process_ced()
