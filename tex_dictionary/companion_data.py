import csv
from dataclasses import dataclass
from typing import Any

from dictionary_pipeline.paths import (
    ASPECT_CLASS_MASCOTS_PATH,
    CLASS_MATCH_COUNTS_PATH,
    CLASSES_DATA_PATH,
)


@dataclass
class AspectClass:
    name: str
    subclass: str
    preconditions: str
    present: str
    imperfective: str
    perfective: str
    imperative: str
    infinitive: str
    frequency: int = 0

    @property
    def full_name(self) -> str:
        if self.subclass:
            return f"{self.name}-{self.subclass}"
        return self.name


def load_aspect_classes() -> list[AspectClass]:
    classes: list[AspectClass] = []
    with open(CLASSES_DATA_PATH, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            classes.append(
                AspectClass(
                    name=row["class"],
                    subclass=row["subclass"],
                    preconditions=row["preconditions"],
                    present=row["present"],
                    imperfective=row["imperfective"],
                    perfective=row["perfective"],
                    imperative=row["imperative"],
                    infinitive=row["infinitive"],
                )
            )
    return classes


def sort_classes_by_frequency(classes: list[AspectClass]) -> list[AspectClass]:
    """
    Sorts the list of aspect classes in descending order of empirical frequency
    based on the artifacts/reports/class_match_counts.csv report.
    """
    match_counts: dict[str, int] = {}
    try:
        with open(CLASS_MATCH_COUNTS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                class_key = row["class"]
                count = int(row["reconstructs"])
                # The report may have multiple entries per class (e.g. if broken down by ending)
                match_counts[class_key] = match_counts.get(class_key, 0) + count
    except FileNotFoundError:
        # Fallback to 0 if the report hasn't been generated yet
        pass

    for cls in classes:
        cls.frequency = match_counts.get(cls.full_name, 0)

    # Sort in descending order of empirical frequency.
    # We use a tuple (frequency, full_name) for sorting.
    # To sort frequency descending and full_name ascending (for stable secondary sort),
    # we can use reverse=True and negate frequency if it was numeric,
    # but since we want descending frequency, reverse=True is fine.
    # For full_name we'd want it ascending if frequency is equal.
    return sorted(
        classes,
        key=lambda x: (x.frequency, [-ord(c) for c in x.full_name]),
        reverse=True,
    )


def load_mascot_map() -> dict[str, str]:
    """
    Loads the curated mascot mapping from curated/aspect_class_mascots.csv.
    Returns a dictionary mapping class full_name to mascot_corpus_id.
    """
    mascot_map: dict[str, str] = {}
    try:
        with open(ASPECT_CLASS_MASCOTS_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                class_key = (
                    f"{row['class']}-{row['subclass']}"
                    if row["subclass"]
                    else row["class"]
                )
                if row["mascot_corpus_id"]:
                    mascot_map[class_key] = row["mascot_corpus_id"]
    except FileNotFoundError:
        pass
    return mascot_map


def select_deterministic_mascot(
    candidate_verbs: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Deterministic fallback for mascot selection: pick the alphabetically first occurring
    verb by its present form.
    """
    if not candidate_verbs:
        raise ValueError("No candidate verbs provided for mascot selection.")
    # Use 'present' field for alphabetical sort.
    return sorted(candidate_verbs, key=lambda x: str(x.get("present", "")))[0]


if __name__ == "__main__":
    # Quick validation
    classes = load_aspect_classes()
    sorted_classes = sort_classes_by_frequency(classes)
    print(f"Loaded {len(classes)} classes.")
    print("Top 5 classes by frequency:")
    for cls in sorted_classes[:5]:
        print(f"{cls.full_name}: {cls.frequency}")

    mascots = load_mascot_map()
    print(f"Loaded {len(mascots)} curated mascots.")
