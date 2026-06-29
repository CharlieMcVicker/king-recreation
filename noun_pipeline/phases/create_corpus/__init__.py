import csv
import os
from typing import Any, Dict

from dictionary_pipeline.utils import clean_string, read_original_cnd

# Define paths relative to the repository root
CHEROKEE_NATION_DICTIONARY_PATH = os.path.join("data", "cherokee_nation_dictionary.csv")
NOUNS_CORPUS_PATH = os.path.join("artifacts", "corpora", "nouns_corpus.csv")


def is_plural(row: Dict[str, str]) -> bool:
    sub = row.get("Grammar sub entry", "").strip().lower()
    if "plural" in sub:
        return True
    if "singular" in sub:
        return False
    transl = row.get("Translation 1A", "").strip().lower()
    if transl.endswith("s") or "people" in transl:
        return True
    return False


def get_animate_flag(row: Dict[str, str]) -> str:
    sub = row.get("Grammar sub entry", "").strip().lower()
    trans = row.get("Translation 1 sub entry", "").strip().lower()

    if "inanimate" in sub or "inanimate" in trans:
        return "inanimate"
    if "animate" in sub or "animate" in trans:
        return "animate"
    return ""


def create_corpus() -> None:
    """
    Load noun entries from Cherokee Nation Dictionary, group singular/plural
    variants under the same entry, preserve the 'animate' flag, and save the noun corpus.
    """
    rows = read_original_cnd()

    # Group rows by "No." for nouns
    grouped_entries = {}
    for row in rows:
        pos = row.get("Part of speech", "").lower().strip()
        if pos != "noun":
            continue

        entry_no = row.get("No.", "").strip()
        if not entry_no:
            continue

        if entry_no not in grouped_entries:
            grouped_entries[entry_no] = []
        grouped_entries[entry_no].append(row)

    processed_data = []
    corpus_idx = 0

    for entry_no, entry_rows in sorted(
        grouped_entries.items(), key=lambda x: int(x[0]) if x[0].isdigit() else x[0]
    ):
        # Separate singular and plural rows within the entry group
        singular_rows = [r for r in entry_rows if not is_plural(r)]
        plural_rows = [r for r in entry_rows if is_plural(r)]

        # Get definition from the group (prefer singular row, fallback to first row with definition)
        definition = ""
        for r in singular_rows + plural_rows + entry_rows:
            gloss = r.get("Translation 1A", "").strip()
            extra = r.get("Translation 1 sub entry", "").strip()
            if extra:
                gloss = f"{gloss} ({extra})"
            if gloss:
                definition = gloss
                break

        # If no definition found yet, try other columns
        if not definition:
            for r in entry_rows:
                for col in ["Translation 1B", "English gloss 1", "English gloss 2"]:
                    val = r.get(col, "").strip()
                    if val:
                        definition = val
                        break
                if definition:
                    break

        def make_row(
            s_row: Dict[str, str] = None, p_row: Dict[str, str] = None
        ) -> Dict[str, Any]:
            s_val = clean_string(s_row.get("Practical", "")) if s_row else ""
            p_val = clean_string(p_row.get("Practical", "")) if p_row else ""

            # Resolve animate flag. Prioritize specific row values if present.
            animate_flag = ""
            if s_row:
                animate_flag = get_animate_flag(s_row)
            if not animate_flag and p_row:
                animate_flag = get_animate_flag(p_row)

            return {
                "corpus_id": str(corpus_idx),
                "entry_no": entry_no,
                "definition": definition,
                "singular": s_val,
                "plural": p_val,
                "animate": animate_flag,
            }

        # Pair singular and plural variants
        if singular_rows and plural_rows:
            for s_row in singular_rows:
                for p_row in plural_rows:
                    processed_data.append(make_row(s_row, p_row))
                    corpus_idx += 1
        elif singular_rows:
            for s_row in singular_rows:
                processed_data.append(make_row(s_row=s_row))
                corpus_idx += 1
        elif plural_rows:
            for p_row in plural_rows:
                processed_data.append(make_row(p_row=p_row))
                corpus_idx += 1

    # Write to CSV
    os.makedirs(os.path.dirname(NOUNS_CORPUS_PATH), exist_ok=True)
    fieldnames = [
        "corpus_id",
        "entry_no",
        "definition",
        "singular",
        "plural",
        "animate",
    ]
    with open(NOUNS_CORPUS_PATH, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(processed_data)

    print(
        f"Created noun corpus with {len(processed_data)} entries at {NOUNS_CORPUS_PATH}"
    )


if __name__ == "__main__":
    create_corpus()
