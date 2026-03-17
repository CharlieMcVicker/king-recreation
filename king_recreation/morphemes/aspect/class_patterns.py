import itertools
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from king_recreation.h_alternation import (
    possible_alternates,
    prevent_C_glottal_cluster,
    recreate_C_glottal_clusters,
)
from king_recreation.morphemes.aspect.strip import StrippedVerbRow
from king_recreation.phonology_data import VOWEL_SET
from king_recreation.word_spec import FORM_NAME_TO_ASPECT


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

    preconditions: Tuple[str, ...] = field(default_factory=tuple)

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
        for alt_suffix in possible_alternates(suffix, fix_clusters=False):
            if self._match_ending(recreate_C_glottal_clusters(form_val), alt_suffix):
                return True

        return False

    def match_ending(self, forms: dict[str, str], form_name: str):
        return self._match_ending(
            suffix=self.get(form_name), form_val=forms.get(form_name)
        )

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

    def strip_verb(self, verb) -> Optional[StrippedVerbRow]:
        # Create stripped row

        stripped_row = StrippedVerbRow(
            corpus_id=verb.get("corpus_id", ""),
            definition=verb.get("definition", ""),
            verb_class=self.name,
        )

        # Strip suffixes
        forms = [
            "present",
            "present_1sg",
            "imperfective",
            "perfective",
            "imperative",
            "infinitive",
        ]
        for fn in forms:
            form_val = verb.get(fn)
            if not form_val:
                continue

            aspect = FORM_NAME_TO_ASPECT.get(fn, fn)
            cls_pattern = self.get(aspect)

            if cls_pattern is None:
                cls_pattern = ""

            # Strip Literal Suffix
            literal_suffix = cls_pattern.replace("*", "").replace("@", "")

            if form_val.endswith(literal_suffix):
                stripped_stem = (
                    form_val[: -len(literal_suffix)] if literal_suffix else form_val
                )
                setattr(stripped_row, fn, stripped_stem)

            # allow h alternates
            elif aspect in ["present", "imperative"]:
                for hless_suffix in possible_alternates(
                    literal_suffix, fix_clusters=False
                ):
                    fixed_hless_suffix = prevent_C_glottal_cluster(hless_suffix)
                    if form_val.endswith(fixed_hless_suffix):
                        stripped_stem = (
                            form_val[: -len(fixed_hless_suffix)]
                            if fixed_hless_suffix
                            else form_val
                        )
                        setattr(stripped_row, fn, stripped_stem)
                    elif hless_suffix.startswith("'"):
                        form_with_glottals = recreate_C_glottal_clusters(form_val)
                        if form_with_glottals.endswith(hless_suffix):
                            stripped_stem = (
                                form_with_glottals[: -len(hless_suffix)]
                                if hless_suffix
                                else form_with_glottals
                            )
                            setattr(
                                stripped_row,
                                fn,
                                prevent_C_glottal_cluster(stripped_stem),
                            )

        return stripped_row


@dataclass
class ClassMacro:
    """
    Represents a raw row from the CSV where fields can contain multiple options (semicolon-separated).
    """

    parent_name: str
    name: str
    present: List[str]
    imperfective: List[str]
    perfective: List[str]
    imperative: List[str]
    infinitive: List[str]

    preconditions: List[str]

    _original_data: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def from_row(row: Dict[str, str]) -> "ClassMacro":
        parent_name = row.get("class", "")
        subname = row.get("subclass", "")
        if subname:
            name = f"{parent_name}-{subname}"
        else:
            name = parent_name

        def parse_field(field_name):
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

            expanded_patterns.append(ExpandedClassPattern(**expanded_data))

        return expanded_patterns
