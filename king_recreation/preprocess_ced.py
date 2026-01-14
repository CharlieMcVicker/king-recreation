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

    return s


def clean_string(s):
    if not s or s == "-----":
        return ""
    # Remove tones [1234] and glottal stops [?] and periods [.]
    # README says tone markings /[1234\.]/ and glottal stops /\?/
    s = re.sub(r"[1234\.\?]", "", s)
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
    process_ced()
