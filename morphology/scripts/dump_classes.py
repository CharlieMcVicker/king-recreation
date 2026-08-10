import csv

from morphology.morphemes.aspect.pattern_registry import CLASSES_PATH, PatternRegistry


def main():
    registry = PatternRegistry.get_instance()
    registry.load_from_csv(CLASSES_PATH)

    with open("artifacts/expanded_classes.csv", "w+") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class",
                "preconditions",
                "present",
                "imperfective",
                "perfective",
                "imperative",
                "infinitive",
            ],
        )
        writer.writeheader()
        for pattern in registry.expanded_patterns:
            writer.writerow(
                {
                    "class": pattern.name,
                    "preconditions": ";".join(pattern.preconditions),
                    "present": pattern.present,
                    "imperfective": pattern.imperfective,
                    "perfective": pattern.perfective,
                    "imperative": pattern.imperative,
                    "infinitive": pattern.infinitive,
                }
            )


if __name__ == "__main__":
    main()
