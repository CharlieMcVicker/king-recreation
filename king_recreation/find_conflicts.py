import csv
from collections import defaultdict


def find_conflicts(file_path):
    print(
        f"Scanning {file_path} for entries with multiple 1st person or imperative forms..."
    )

    entries = defaultdict(list)

    with open(file_path, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            entry_no = row.get("No.", "").strip()
            if entry_no:
                entries[entry_no].append(row)

    conflicts_found = 0
    for entry_no, rows in entries.items():
        person1_forms = []
        imperative_forms = []

        for row in rows:
            sub = row.get("Grammar sub entry", "").lower()
            if "1st person" in sub:
                person1_forms.append(sub)
            if "imperative" in sub:
                imperative_forms.append(sub)

        if len(person1_forms) > 1:
            print(f"Entry {entry_no}: Multiple 1st person forms: {person1_forms}")
            conflicts_found += 1

        if len(imperative_forms) > 1:
            print(f"Entry {entry_no}: Multiple imperative forms: {imperative_forms}")
            conflicts_found += 1

    print(f"Found {conflicts_found} entries with potential conflicts.")


if __name__ == "__main__":
    from king_recreation.paths import cherokee_nation_dictionary_path

    find_conflicts(cherokee_nation_dictionary_path)
