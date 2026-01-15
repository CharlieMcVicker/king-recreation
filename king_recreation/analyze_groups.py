import csv
import os


def analyze_cn_dict(file_path):
    print(f"Analyzing Cherokee Nation dictionary from {file_path}")

    if not os.path.exists(file_path):
        print(f"Error: Input file needed not found at {file_path}")
        return

    # Group rows by "Entry No."
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

    verb_groups = 0
    missing_present_count = 0
    sparse_groups = []

    # Forms we care about
    # "3rd person singular" -> present
    # "1st person singular" -> present_1sg
    # "3rd person singular present habitual" -> imperfective
    # "3rd person singular non-progressive remote past tense" -> perfective
    # "imperative" -> imperative
    # "3rd person singular infinitive" -> infinitive

    print("\n--- Analysis of Verb Groups ---")

    for entry_no, rows in grouped_entries.items():
        is_verb = False
        for row in rows:
            pos = row.get("Part of speech", "").lower()
            if pos.startswith("verb"):
                is_verb = True
                break

        if not is_verb:
            continue

        verb_groups += 1

        forms_found = {
            "present": False,
            "present_1sg": False,
            "imperfective": False,
            "perfective": False,
            "imperative": False,
            "infinitive": False,
        }

        definition = ""
        for row in rows:
            gloss = row.get("English gloss 1", "").strip()
            if gloss:
                definition = gloss
                break

        for row in rows:
            sub_entry = row.get("Grammar sub entry", "").strip().lower()
            practical_form = row.get("Practical", "").strip()

            if not practical_form:
                continue

            if sub_entry.startswith("3rd person singular"):
                if "habitual" in sub_entry:
                    forms_found["imperfective"] = True
                elif "remote past" in sub_entry:
                    forms_found["perfective"] = True
                elif "infinitive" in sub_entry:
                    forms_found["infinitive"] = True
                else:
                    forms_found["present"] = True
            elif sub_entry.startswith("1st person singular"):
                forms_found["present_1sg"] = True
            elif sub_entry.startswith("imperative"):
                forms_found["imperative"] = True

        filled_slots = sum(1 for v in forms_found.values() if v)

        if not forms_found["present"]:
            missing_present_count += 1
            sparse_groups.append(
                {
                    "entry_no": entry_no,
                    "definition": definition,
                    "forms_count": filled_slots,
                    "forms_found": [k for k, v in forms_found.items() if v],
                }
            )
        elif filled_slots <= 2:
            # Also track very sparse verbs even if they have present (e.g. only present + 1 other)
            sparse_groups.append(
                {
                    "entry_no": entry_no,
                    "definition": definition,
                    "forms_count": filled_slots,
                    "forms_found": [k for k, v in forms_found.items() if v],
                }
            )

    print(f"Total Verb Groups Found: {verb_groups}")
    print(f"Groups Missing 3rd Person Present: {missing_present_count}")
    print(
        f"Groups with <= 2 identified major forms (or missing present): {len(sparse_groups)}"
    )

    print("\n--- Sample of Problematic Verbs ---")
    # Sort by entry number float value roughly
    try:
        sparse_groups.sort(key=lambda x: float(x["entry_no"]))
    except:
        pass  # Ignore sort errors if alphanumeric

    for group in sparse_groups[:20]:
        print(
            f"Entry {group['entry_no']} ({group['definition']}): Found {group['forms_count']} forms {group['forms_found']}"
        )

    if len(sparse_groups) > 20:
        print(f"... and {len(sparse_groups) - 20} more.")


if __name__ == "__main__":
    analyze_cn_dict("data/cherokee_nation_dictionary.csv")
