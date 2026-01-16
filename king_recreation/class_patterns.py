from dataclasses import dataclass, field
from typing import List, Dict, Optional
import itertools
import re


@dataclass(frozen=True)
class ExpandedClassPattern:
    """
    Represents a single, fully resolved pattern (no lists).
    """

    name: str
    stem_finals: tuple
    present: str
    imperfective: str
    perfective: str
    imperative: str
    infinitive: str

    # Store original row just in case we need extra fields later without breaking changes
    _original_data: Dict[str, str] = field(default=None, hash=False, compare=False)

    def macro_name(self):
        return self._original_data.get("class", self.name)

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


@dataclass
class ClassMacro:
    """
    Represents a raw row from the CSV where fields can contain multiple options (semicolon-separated).
    """

    name: str
    stem_finals: List[str]
    present: List[str]
    imperfective: List[str]
    perfective: List[str]
    imperative: List[str]
    infinitive: List[str]
    _original_data: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_row(row: Dict[str, str]) -> "ClassMacro":
        name = row.get("class", "")
        sf_raw = row.get("stem final", "")
        sf_list = [s for s in sf_raw.split(";") if s] if sf_raw else [""]

        def parse_field(field_name):
            val = row.get(field_name, "")
            return [v.strip() for v in val.split(";")]

        return ClassMacro(
            name=name,
            stem_finals=sf_list,
            present=parse_field("present"),
            imperfective=parse_field("imperfective"),
            perfective=parse_field("perfective"),
            imperative=parse_field("imperative"),
            infinitive=parse_field("infinitive"),
            _original_data=row,
        )

    def expand(self) -> List[ExpandedClassPattern]:
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

        # Prepare options for Cartesian product
        field_options = []
        for field in form_fields:
            # Get list of options from self
            options = getattr(self, field)
            # Enumerate to track variant indices (1-based)
            field_options.append(list(enumerate(options, 1)))

        expanded_patterns = []
        # Cartesian product of options
        for combo in itertools.product(*field_options):
            # combo is a list of (index, value) tuples corresponding to form_fields order

            expanded_data = {
                "name": self.name,
                "stem_finals": tuple(self.stem_finals),
                "_original_data": self._original_data,
            }
            suffixes = []

            for i, (variant_idx, variant_val) in enumerate(combo):
                field_name = form_fields[i]
                expanded_data[field_name] = variant_val

                # If it's the 2nd (or later) variant, add a suffix tag
                if variant_idx > 1:
                    tag = f"{shorthands[field_name]}{variant_idx}"
                    suffixes.append(tag)

            if suffixes:
                expanded_data["name"] = f"{self.name}[{'-'.join(suffixes)}]"

            expanded_patterns.append(ExpandedClassPattern(**expanded_data))

        return expanded_patterns
