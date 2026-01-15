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
    ]
    for old, new in rules:
        s = s.replace(old, new)

    s = re.sub(r"sl(?=[aeiouv])", "slh", s)

    return s


def clean_string(s):
    if not s or s == "-----":
        return ""
    # Remove tones [1234], glottal stops [?], periods [.], and apostrophes ['’] (which are glottal stops in new source)
    # README says tone markings /[1234\.]/ and glottal stops /\?/
    s = re.sub(r"[1234\.\?'’]", "", s)
    return respell_consonants(s)


def clean_row(row):
    definition = row.get("definition", "").strip()

    present = clean_string(row.get("3rd present", ""))
    # README: "3rd present column with final i or a rstripped; for ia only a is dropped"
    if present.endswith("ia"):
        present = present[:-1]
    elif present.endswith("i") or present.endswith("a"):
        present = present[:-1]

    present_1sg = clean_string(row.get("1st present", ""))
    # Same logic as 3rd present: strip final i or a
    if present_1sg.endswith("ia"):
        present_1sg = present_1sg[:-1]
    elif present_1sg.endswith("i") or present_1sg.endswith("a"):
        present_1sg = present_1sg[:-1]

    imperfective_raw = row.get("3rd incompletive habitual", "")
    imperfective = clean_string(imperfective_raw)
    # README: "3rd incompletive habitual column with oi rstripped"
    # Logic: if it ends in 'i' (possibly with tones/glottals), and has 'o' before it.
    if imperfective.endswith("oi"):
        imperfective = imperfective[:-2]

    perfective_raw = row.get("3rd completive past", "")
    perfective = clean_string(perfective_raw)
    # README: "3rd completive past column with vi rstripped"
    if perfective.endswith("vi"):
        perfective = perfective[:-2]

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

    for entry_no, rows in grouped_entries.items():
        # Build a single verb dictionary from the rows
        verb_data = {
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

        # Dictionary to store the best form found so far for each slot
        # Structure: slot_name -> (form, priority)
        # Priority: 2 = animate/3rd person object, 1 = inanimate, 0 = generic/unspecified
        best_forms = {
            "present": ("", -1),
            "present_1sg": ("", -1),
            "imperfective": ("", -1),
            "perfective": ("", -1),
            "imperative": ("", -1),
            "infinitive": ("", -1),
        }

        # Helper to update best form
        def update_form(slot, form, sub_entry_text):
            priority = 0
            sub_lower = sub_entry_text.lower()
            if "animate" in sub_lower and "inanimate" not in sub_lower:
                priority = 2
            elif "animate" in sub_lower:
                # "animate/ inanimate" usually means generic or covers both, treat as high priority if explicit purely animate isn't splitting
                # But looking at conflicts "animate" vs "inanimate", usually "animate" is better.
                # "1st person singular with animate object" vs "1st person singular with inanimate object"
                if "with animate object" in sub_lower:
                    priority = 2
                elif "animate/ inanimate" in sub_lower:
                    # This is effectively generic or combined.
                    # Let's say: strictly animate > animate/inanimate > inanimate > unknown
                    priority = 1.5
            elif "inanimate" in sub_lower:
                priority = 1

            # 3rd person object check (user request) - usually covered by 'animate' but just in case
            if "3rd person object" in sub_lower:
                priority = 2

            current_form, current_priority = best_forms[slot]
            if priority > current_priority:
                best_forms[slot] = (form, priority)
            elif priority == current_priority:
                # If equal priority, maybe prefer the one that doesn't say "inanimate" if we haven't distinguished?
                # For now, first come first serve or overwrite?
                # Let's overwrite to be safe, or stick with first.
                # Actually, usually there's a clear winner. If priorities are equal (e.g. both generic), it doesn't matter much.
                best_forms[slot] = (form, priority)

        # Map forms based on "Grammar sub entry"
        for row in rows:
            sub_entry = row.get("Grammar sub entry", "").strip().lower()
            practical_form = row.get("Practical", "").strip()

            if not practical_form:
                continue

            clean_form = clean_string(practical_form)

            # Mapping logic with loose matching
            if sub_entry.startswith("3rd person singular"):
                # Distinguish from potential other 3rd person forms if any, but usually this is present
                # Exclude explicit past/habitual/infinitive which start with same prefix
                if "habitual" in sub_entry:
                    update_form("imperfective", clean_form, sub_entry)
                elif "remote past" in sub_entry:
                    update_form("perfective", clean_form, sub_entry)
                elif "infinitive" in sub_entry:
                    update_form("infinitive", clean_form, sub_entry)
                else:
                    # Pure 3rd person singular (present)
                    update_form("present", clean_form, sub_entry)

            elif sub_entry.startswith("1st person singular"):
                update_form("present_1sg", clean_form, sub_entry)

            elif "imperative" in sub_entry and "2nd person" not in sub_entry:
                # Sometimes just "imperative ...", sometimes "2nd person imperative"?
                # In CN dict, it looks like "imperative with ..."
                update_form("imperative", clean_form, sub_entry)

        # Extract final forms from best_forms
        verb_data["present"] = best_forms["present"][0]
        verb_data["present_1sg"] = best_forms["present_1sg"][0]
        verb_data["imperfective"] = best_forms["imperfective"][0]
        verb_data["perfective"] = best_forms["perfective"][0]
        verb_data["imperative"] = best_forms["imperative"][0]
        verb_data["infinitive"] = best_forms["infinitive"][0]

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
        if p.endswith("ia"):
            verb_data["present"] = p[:-1]
        elif p.endswith("i") or p.endswith("a"):
            verb_data["present"] = p[:-1]

        # Present 1sg
        p1 = verb_data["present_1sg"]
        if p1.endswith("ia"):
            verb_data["present_1sg"] = p1[:-1]
        elif p1.endswith("i") or p1.endswith("a"):
            verb_data["present_1sg"] = p1[:-1]

        # Imperfective
        imp = verb_data["imperfective"]
        if imp.endswith("oi"):
            verb_data["imperfective"] = imp[:-2]

        # Perfective
        perf = verb_data["perfective"]
        if perf.endswith("vi"):
            verb_data["perfective"] = perf[:-2]

        # Infinitive
        inf = verb_data["infinitive"]
        if inf.endswith("i"):
            verb_data["infinitive"] = inf[:-1]

        # Only add if we have at least a present form or something substantial?
        # The existing logic doesn't explicitly filter but empty strings result in empty columns.
        processed_data.append(verb_data)

    fieldnames = [
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
        for row in reader:
            processed_data.append(clean_row(row))

    fieldnames = [
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
