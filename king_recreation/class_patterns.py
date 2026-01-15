from dataclasses import dataclass
from typing import List, Dict, Optional
import csv
import os


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
                sf_raw = row.get("stem final", "")
                # Split on semicolon, filter empty
                sf_list = [s for s in sf_raw.split(";") if s] if sf_raw else [""]

                name = row.get("class", "")
                patterns[name] = ClassPatterns(
                    name=name,
                    stem_finals=sf_list,
                    present=row.get("present", ""),
                    imperfective=row.get("imperfective", ""),
                    perfective=row.get("perfective", ""),
                    imperative=row.get("imperative", ""),
                    infinitive=row.get("infinitive", ""),
                    _original_data=row,
                )
        return patterns
