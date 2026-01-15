from dataclasses import dataclass
from typing import List, Dict, Optional
import csv
import os
import itertools


@dataclass
class ClassPatterns:
    name: str
    stem_finals: List[str]
    present: str
    imperfective: str
    perfective: str
    imperative: str
    infinitive: str

    # Store original row just in case we need extra fields later without breaking changes
    _original_data: Dict[str, str] = None

    def get(self, form: str, default: str = "") -> str:
        """
        Mimics dict.get() for backward compatibility and dynamic access.
        """
        if form == "class":
            return self.name
        if hasattr(self, form):
            val = getattr(self, form)
            return val if val is not None else default
        return default

    @staticmethod
    def from_csv(path: str) -> Dict[str, "ClassPatterns"]:
        patterns = {}
        if not os.path.exists(path):
            print(f"Warning: Class patterns file not found at {path}")
            return patterns

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for pattern in ClassPatterns._expand_row(row):
                    patterns[pattern.name] = pattern

        return patterns

    @staticmethod
    def _expand_row(row: Dict[str, str]) -> List["ClassPatterns"]:
        shorthands = {
            "present": "pres",
            "imperfective": "imperf",
            "perfective": "perf",
            "imperative": "imp",
            "infinitive": "inf",
        }
        form_fields = [
            "present",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]

        name = row.get("class", "")
        sf_raw = row.get("stem final", "")
        sf_list = [s for s in sf_raw.split(";") if s] if sf_raw else [""]

        # Prepare options for each field
        field_options = []
        for field in form_fields:
            val = row.get(field, "")
            options = [v.strip() for v in val.split(";")]
            field_options.append(list(enumerate(options, 1)))

        expanded_patterns = []
        # Cartesian product of options
        for combo in itertools.product(*field_options):
            # combo is a list of (index, value) tuples
            expanded_data = {
                "name": name,
                "stem_finals": sf_list,
                "_original_data": row,
            }
            suffixes = []

            for i, (field_idx, field_val) in enumerate(combo):
                field_name = form_fields[i]
                expanded_data[field_name] = field_val
                if field_idx > 1:
                    tag = f"{shorthands[field_name]}{field_idx}"
                    suffixes.append(tag)

            if suffixes:
                expanded_data["name"] = f"{name}[{'-'.join(suffixes)}]"

            expanded_patterns.append(ClassPatterns(**expanded_data))

        return expanded_patterns
