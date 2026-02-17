import csv
import os

from king_recreation.paths import (
    CED_DATA_ORIGINAL_PATH,
    CHEROKEE_NATION_DICTIONARY_PATH,
    CORPUS_PATH,
    CORPUS_RAW_PATH,
    CORPUS_TO_CND_PATH,
    MANUAL_CORRECTIONS_PATH,
)


def ensure_output_dir():
    output_data_dir = os.path.dirname(CORPUS_PATH)
    if not os.path.exists(output_data_dir):
        os.makedirs(output_data_dir)


def read_original_ced():
    data = []
    if not os.path.exists(CED_DATA_ORIGINAL_PATH):
        return []
    with open(CED_DATA_ORIGINAL_PATH, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def read_original_cnd():
    if not os.path.exists(CHEROKEE_NATION_DICTIONARY_PATH):
        raise FileNotFoundError(
            f"Input file not found at {CHEROKEE_NATION_DICTIONARY_PATH}"
        )

    with open(CHEROKEE_NATION_DICTIONARY_PATH, mode="r", encoding="utf-8") as f:
        content = f.read()
        if content.startswith("\ufeff"):
            content = content[1:]
        import io

        return list(csv.DictReader(io.StringIO(content)))


def save_corpus(data: list, fieldnames: list):
    ensure_output_dir()
    with open(CORPUS_PATH, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Processed data written to {CORPUS_PATH}")


def save_raw_corpus(data: list, fieldnames: list):
    ensure_output_dir()
    with open(CORPUS_RAW_PATH, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Raw processed data written to {CORPUS_RAW_PATH}")


def load_manual_corrections() -> list[dict]:
    if not os.path.exists(MANUAL_CORRECTIONS_PATH):
        return []
    with open(MANUAL_CORRECTIONS_PATH, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_corpus() -> list[dict]:
    if not os.path.exists(CORPUS_PATH):
        return []
    with open(CORPUS_PATH, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def save_mapping(data: list, fieldnames: list):
    ensure_output_dir()
    with open(CORPUS_TO_CND_PATH, mode="w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    print(f"Mapping CND data written to {CORPUS_TO_CND_PATH}")


def load_mapping() -> list[dict]:
    if not os.path.exists(CORPUS_TO_CND_PATH):
        return []
    with open(CORPUS_TO_CND_PATH, mode="r", encoding="utf-8") as f:
        return list(csv.DictReader(f))
