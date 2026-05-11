import itertools
from dataclasses import dataclass, field
from typing import Any

from king_recreation.h_alternation import (
    possible_alternates,
    prevent_C_glottal_cluster,
    recreate_C_glottal_clusters,
)
from king_recreation.morphology_types import Aspect
from king_recreation.phonology_data import VOWEL_SET


@dataclass(frozen=True)
class ExpandedClassPattern:
    """
    Represents a single, fully resolved pattern (no lists).
    """

    parent_name: str
    name: str
    present: str
    imperfective: str
    perfective: str
    imperative: str
    infinitive: str

    preconditions: tuple[str, ...] = field(default_factory=tuple)

    # Store original row just in case we need extra fields later without breaking changes
    _original_data: dict[str, str] | None = field(
        default=None, hash=False, compare=False
    )

    def macro_name(self) -> str:
        if self._original_data is None:
            return self.name
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

    def check_preconditions(
        self, preceding_text: str, suffix_val: str = "", h_alternated_form: bool = False
    ) -> bool:
        if "*" in suffix_val or "@" in suffix_val:
            return True

        if not self.preconditions or not len(self.preconditions):
            return True

        # Vacuous match if no preceding text (suffix consumes entire string)
        if not preceding_text:
            return True

        for p in self.preconditions:
            if self._match_sequence(p, preceding_text, h_alternated_form):
                return True

        return False

    def _match_sequence(
        self, sequence: str, text: str, h_alternated_form: bool
    ) -> bool:
        if len(text) < len(sequence):
            return False

        if h_alternated_form:
            for seq in possible_alternates(sequence):
                if self._match_sequence(seq, text, False):
                    return True
            else:
                return False

        for i in range(1, len(sequence) + 1):
            s_char = sequence[-i]
            t_char = text[-i]
            if s_char == "V":
                if t_char not in VOWEL_SET:
                    return False
            elif s_char == "C":
                if t_char in VOWEL_SET:
                    return False
            else:
                # Literal match
                if t_char != s_char:
                    return False
        return True

    def match_alternated_endings(self, forms: dict[str, str], form_name: str):
        suffix = self.get(form_name)
        form_val = forms.get(form_name)
        if form_val is None:
            raise ValueError(f"No value for form {form_name}")
        for alt_suffix in possible_alternates(suffix, fix_clusters=False):
            if self._match_ending(recreate_C_glottal_clusters(form_val), alt_suffix):
                return True

        return False

    def match_ending(self, forms: dict[str, str], form_name: str):
        form_val = forms.get(form_name)
        if form_val is None:
            raise ValueError(f"No value for form {form_name}")
        return self._match_ending(suffix=self.get(form_name), form_val=form_val)

    def _match_ending(self, form_val: str, suffix: str):
        # Policy: Vacuous Matching
        # If the corpus form is missing, it cannot contradict any pattern.
        if not form_val:
            return True

        # Literal characters only, ignore * or @
        if suffix is None:
            suffix = ""
        literal_suffix = suffix.replace("*", "").replace("@", "")

        return form_val.endswith(literal_suffix)

    def strip_form(self, aspect: Aspect, form_val: str) -> str | None:
        """
        Strip the aspect suffix for a given aspect from a surface form value.

        Returns the stripped stem, or None if no suffix match was found.
        This is a pure morphological operation — no dictionary column awareness.
        """
        if not form_val:
            return None

        cls_pattern = self.get(aspect.value)

        if cls_pattern is None:
            cls_pattern = ""

        # Strip Literal Suffix
        literal_suffix = cls_pattern.replace("*", "").replace("@", "")

        if form_val.endswith(literal_suffix):
            return form_val[: -len(literal_suffix)] if literal_suffix else form_val

        # Allow h alternates for aspects that permit h-alternation.
        # Sort by length descending so we greedily match the longest alternate
        # first (e.g. strip 'vsk before vsk to avoid leaving a trailing glottal).
        if aspect.allows_h_alternation:
            alternates = sorted(
                possible_alternates(literal_suffix, fix_clusters=False),
                key=len,
                reverse=True,
            )
            for hless_suffix in alternates:
                fixed_hless_suffix = prevent_C_glottal_cluster(hless_suffix)
                if form_val.endswith(fixed_hless_suffix):
                    return (
                        form_val[: -len(fixed_hless_suffix)]
                        if fixed_hless_suffix
                        else form_val
                    )
                elif hless_suffix.startswith("'"):
                    form_with_glottals = recreate_C_glottal_clusters(form_val)
                    if form_with_glottals.endswith(hless_suffix):
                        stripped_stem = (
                            form_with_glottals[: -len(hless_suffix)]
                            if hless_suffix
                            else form_with_glottals
                        )
                        return prevent_C_glottal_cluster(stripped_stem)

        return None


@dataclass
class ClassMacro:
    """
    Represents a raw row from the CSV where fields can contain multiple options (semicolon-separated).
    """

    parent_name: str
    name: str
    present: list[str]
    imperfective: list[str]
    perfective: list[str]
    imperative: list[str]
    infinitive: list[str]

    preconditions: list[str]

    _original_data: dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_row(row: dict[str, str]) -> "ClassMacro":
        parent_name = row.get("class", "")
        subname = row.get("subclass", "")
        if subname:
            name = f"{parent_name}-{subname}"
        else:
            name = parent_name

        def parse_field(field_name: str) -> list[str]:
            val = row.get(field_name, "")
            return [v.strip() for v in val.split(";")]

        return ClassMacro(
            parent_name=parent_name,
            name=name,
            present=parse_field("present"),
            imperfective=parse_field("imperfective"),
            perfective=parse_field("perfective"),
            imperative=parse_field("imperative"),
            infinitive=parse_field("infinitive"),
            preconditions=[p for p in parse_field("preconditions") if p],
            _original_data=row,
        )

    def expand(self) -> list[ExpandedClassPattern]:
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

            expanded_data: dict[str, Any] = {
                "parent_name": self.parent_name,
                "name": self.name,
                "preconditions": tuple(self.preconditions),
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

            expanded_patterns.append(
                ExpandedClassPattern(
                    parent_name=expanded_data["parent_name"],
                    name=expanded_data["name"],
                    preconditions=expanded_data["preconditions"],
                    _original_data=expanded_data["_original_data"],
                    present=expanded_data["present"],
                    imperfective=expanded_data["imperfective"],
                    perfective=expanded_data["perfective"],
                    imperative=expanded_data["imperative"],
                    infinitive=expanded_data["infinitive"],
                )
            )

        return expanded_patterns
