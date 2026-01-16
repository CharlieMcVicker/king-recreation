from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import csv
import os
import re
from collections import defaultdict
from king_recreation.class_patterns import ClassMacro, ExpandedClassPattern

CLASSES_PATH = "data/classes.csv"


class PatternRegistry:
    _instance = None

    def __init__(self):
        self.macros: List[ClassMacro] = []
        self.macros_order = {}
        self.expanded_patterns: List[ExpandedClassPattern] = []
        # Map[form_type, Map[ending_string, List[ExpandedClassPattern]]]
        self.lookup_maps: Dict[str, Dict[str, List[ExpandedClassPattern]]] = (
            defaultdict(lambda: defaultdict(list))
        )
        # Keep track of all valid ending lengths to optimize substring checks
        self.valid_ending_lengths: Dict[str, set] = defaultdict(set)

    @classmethod
    def get_instance(cls) -> "PatternRegistry":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def macro_key(self, macro_name):
        return (self.macros_order.get(macro_name, 999),)

    def key_for_pattern_name(self, pattern_name: str) -> tuple:
        # Regex captures the base name and then the digits for each form if present
        # eg. v'vsk[perf2-inf2]
        # --> ("v'vsk", 0, 0, 2, 0, 2)
        pattern = r"([\w\-'\*]+)(?:\[(?:pres(\d+))?\-?(?:imperf(\d+))?\-?(?:perf(\d+))?\-?(?:imp(\d+))?\-?(?:inf(\d+))?\])?"
        match = re.match(pattern, pattern_name)
        if match:
            return (self.macro_key(match.group(1)),) + tuple(
                int(match.group(i) or 0) for i in range(2, 7)
            )
        return (
            self.macro_key(pattern_name),
            0,
            0,
            0,
            0,
            0,
        )

    def key_for_pattern(self, cls_pattern: ExpandedClassPattern) -> tuple:
        return self.key_for_pattern_name(cls_pattern.name)

    def load_from_csv(self, path: Optional[str] = None):
        if not path:
            path = CLASSES_PATH
        if not os.path.exists(path):
            print(f"Warning: Class patterns file not found at {path}")
            return

        self.macros = []
        self.macros_order = {}
        self.expanded_patterns = []

        # Reset maps
        self.lookup_maps = defaultdict(lambda: defaultdict(list))
        self.valid_ending_lengths = defaultdict(set)

        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                # Create Macro
                macro = ClassMacro.from_row(row)
                self.macros.append(macro)
                self.macros_order[macro.name] = i

                # Expand and Index
                expanded = macro.expand()
                self.expanded_patterns.extend(expanded)

        # Sort all patterns to ensure deterministic order
        self.expanded_patterns.sort(key=lambda p: self.key_for_pattern(p))

        for pattern in self.expanded_patterns:
            self._index_pattern(pattern)

    def _index_pattern(self, pattern: ExpandedClassPattern):
        forms = ["present", "imperfective", "perfective", "imperative", "infinitive"]
        for form in forms:
            pattern_str = pattern.get(form)
            # Remove * and @ for literal match key
            literal_suffix = pattern_str.replace("*", "").replace("@", "")

            self.lookup_maps[form][literal_suffix].append(pattern)
            self.valid_ending_lengths[form].add(len(literal_suffix))

    def get_candidates(
        self, verb_form: str, form_type: str
    ) -> List[ExpandedClassPattern]:
        """
        Returns all patterns that match the ending of the verb_form for the given form_type.
        """
        if not verb_form:
            return []

        candidates = []
        # Check all possible suffix lengths
        # Optimization: match against valid lengths only
        verb_len = len(verb_form)

        # Always check for empty suffix match (if any pattern has empty ending)
        if "" in self.lookup_maps[form_type]:
            candidates.extend(self.lookup_maps[form_type][""])

        sorted_lengths = sorted(
            list(self.valid_ending_lengths[form_type]), reverse=True
        )

        for length in sorted_lengths:
            if length == 0:
                continue  # Handled above
            if length > verb_len:
                continue

            suffix = verb_form[-length:]
            if suffix in self.lookup_maps[form_type]:
                candidates.extend(self.lookup_maps[form_type][suffix])

        return candidates
